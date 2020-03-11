import logging as log
import sys, math
import numpy as np
from copy import deepcopy as copy

# Setting Debug level (can be debug, info, warning, error and critical)
log.basicConfig(stream=sys.stderr, level=log.INFO)

''' Emulation settings '''
DEBUG=True

''' Parameters of processor '''
# Input vector width
N = 8

# Number of range filters in filter unit
M = 4 

# Input buffer depth
IB_DEPTH = 8

# Size of FUVRF in M*elements
FUVRF_SIZE=4

# SIze of VVVRF in N*elements
VVVRF_SIZE=8

# SIze of Trace Buffer in N*elements
TB_SIZE=64

''' Verifying parameters '''
assert math.log(N, 2).is_integer(), "N must be a power of 2" 
assert math.log(M, 2).is_integer(), "N must be a power of 2" 
assert M<=N, "M must be less or equal to N" 

''' Useful functions '''
class struct:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    def __repr__(self):
        return str(self.__dict__)

class CISC():
    # Input buffer class 
    class InputBuffer():
        def __init__(self,N,IB_DEPTH):
            self.buffer=[]
            self.size=IB_DEPTH
            self.config=None
            self.chainId_out = 0
            self.bof_out=True

        def push(self,pushed_vals):
            v_in, eof_in = pushed_vals
            assert list(v_in.shape)==[N], "Input must be Nx1"
            assert len(self.buffer)<=self.size, "Input buffer overflowed"
            log.debug('Vector inserted into input buffer\n'+str(v_in))
            self.buffer.append([v_in,eof_in])

        def pop(self):
            log.debug("Removing element from input buffer")
            assert len(self.buffer)>0, "Input buffer is empty"
            self.bof_out=self.buffer[0][1]
            return self.buffer.pop(0)

        def step(self):
            # Dispatch a new chain if the input buffer is not empty
            # Note that if our FW has 3 chains num_chains will be 4, since we need one "chain" (chainId 0) to work as a pass through
            if len(self.buffer)>0:
                if self.chainId_out<self.config.num_chains:
                    # Go to next element in the input buffer once we dispatched all chains for the previous element
                    if self.chainId_out==self.config.num_chains-1:
                        self.pop()
                        self.chainId_out = 0 if len(self.buffer)==0 else 1 
                    else:
                        self.chainId_out=self.chainId_out+1

            # If the trace buffer is full, we will dispatch chain 0, which is a pass through
            else:
                self.chainId_out=0

            if len(self.buffer)>0:
                v_out, eof_out = self.buffer[0]
            else:
                v_out, eof_out = np.zeros(N), False
            return v_out, eof_out, self.bof_out, self.chainId_out

    # Filter Unit
    class FilterUnit():
        def __init__(self,N,M,FUVRF_SIZE):
            self.v_in=np.zeros(N)
            self.m_out=np.zeros((M,N))
            self.eof_in = False
            self.eof_out = False
            self.bof_in = True
            self.bof_out = True
            self.chainId_in = 0
            self.chainId_out = 0
            self.vrf=np.zeros(FUVRF_SIZE*M)
            self.config=None

        def step(self,input_value):
            # Check if the vector is within M ranges
            cfg=self.config[self.chainId_in]
            log.debug('Filter input:'+str(self.v_in))
            log.debug('Filtering using the following ranges:'+str(self.vrf[cfg.addr*M:cfg.addr*M+M+1]))
            if cfg.filter==1:
                for i in range(M):
                    low_range = self.vrf[cfg.addr*M+i]
                    high_range = self.vrf[cfg.addr*M+i+1]
                    within_range = np.all([self.v_in>low_range, self.v_in<=high_range],axis=0)
                    self.m_out[i]=within_range[:]
            # If we are not filtering, just pass the value through 
            else:
                for i in range(M):
                    self.m_out[i] = self.v_in if i==0 else np.zeros(N)

            self.eof_out, self.bof_out, self.chainId_out = self.eof_in, self.bof_in, self.chainId_in
            self.v_in, self.eof_in, self.bof_in, self.chainId_in = copy(input_value)
            return self.m_out, self.eof_out, self.bof_out, self.chainId_out

    # This block will reduce the matrix along a given axis
    # If M<N, then the results will be padded with zeros
    class MatrixVectorReduce():
        def __init__(self,N,M):
            self.m_in=np.zeros((M,N))
            self.v_out=np.zeros(N)
            self.eof_in = False
            self.eof_out = False
            self.bof_in = True
            self.bof_out = True
            self.chainId_in = 0
            self.chainId_out = 0
            self.config=None

        def step(self,input_value):
            # Reduce matrix along a given axis
            cfg=self.config[self.chainId_in]
            if cfg.axis==0:
                log.debug('Passing first vector through reduce unit')
                self.v_out=self.m_in[0]
            elif cfg.axis==1:
                log.debug('Reducing matrix along N axis (axis = '+str(cfg.axis)+')')
                self.v_out=np.sum(self.m_in,axis=0)
            elif cfg.axis==2:
                log.debug('Reducing matrix along M axis (axis = '+str(cfg.axis)+')')
                self.v_out=np.sum(self.m_in,axis=1)
                if N!=M:
                    log.debug('Padding results with '+str(N-M)+' zeros')
                    self.v_out=np.concatenate((self.v_out,np.zeros(N-M)))

            self.eof_out, self.bof_out, self.chainId_out    = self.eof_in, self.bof_in, self.chainId_in
            self.m_in, self.eof_in, self.bof_in, self.chainId_in = copy(input_value)
            return self.v_out, self.eof_out, self.bof_out, self.chainId_out

    # This block will reduce a vector to a scalar and pad with zeros
    class VectorScalarReduce():
        def __init__(self,N):
            self.v_in=np.zeros(N)
            self.v_out=np.zeros(N)
            self.eof_in = False
            self.eof_out = False
            self.bof_in = True
            self.bof_out = True
            self.chainId_in = 0
            self.chainId_out = 0
            self.config=None

        def step(self,input_value):
            # Reduce matrix along a given axis
            cfg=self.config[self.chainId_in]
            
            if cfg.op==0:
                log.debug('Passing first vector through vs reduce unit')
                self.v_out=self.v_in
            elif cfg.op==1:
                log.debug('Sum vector scalar reduce')
                self.v_out=np.concatenate(([np.sum(self.v_in)],np.zeros(N-1))) 
              
            self.eof_out, self.bof_out, self.chainId_out = self.eof_in, self.bof_in, self.chainId_in
            self.v_in, self.eof_in, self.bof_in, self.chainId_in = copy(input_value)
            return self.v_out, self.eof_out, self.bof_out, self.chainId_out

    # This block will reduce the matrix along a given axis
    class VectorVectorALU():
        def __init__(self,N,VVVRF_SIZE):
            self.v_in=np.zeros(N)
            self.v_out=np.zeros(N)
            self.eof_in = False
            self.eof_out = False
            self.bof_in = False
            self.bof_out = False
            self.chainId_in = 0
            self.chainId_out = 0
            self.vrf=np.zeros(N*VVVRF_SIZE)
            self.config=None
            self.v_out_d1=np.zeros(N)
            self.v_out_d2=np.zeros(N)
            self.eof_out_d1 = False
            self.eof_out_d2 = False
            self.bof_out_d1 = True
            self.bof_out_d2 = True
            self.chainId_out_d2 = 0
            self.chainId_out_d1 = 0

        def step(self,input_value):
            # Delay for 2 cycles, so this FU takes 3 cycles (read, calculate, write)
            self.v_out    = self.v_out_d2
            self.v_out_d2 = self.v_out_d1
            self.eof_out  = self.eof_out_d2
            self.eof_out_d2  = self.eof_out_d1
            self.eof_out_d1  = self.eof_in
            self.bof_out  = self.bof_out_d2
            self.bof_out_d2  = self.bof_out_d1
            self.bof_out_d1  = self.bof_in
            self.chainId_out  = self.chainId_out_d2
            self.chainId_out_d2  = self.chainId_out_d1
            self.chainId_out_d1  = self.chainId_in

            cfg=self.config[self.chainId_in]
            if cfg.op==0:
                log.debug('ALU is passing values through')
                self.v_out_d1 = self.v_in
            elif cfg.op==1:
                if ((not cfg.cond['last']     or (cfg.cond['last']     and     self.eof_in)) and
                    (not cfg.cond['notlast']  or (cfg.cond['notlast']  and not self.eof_in)) and
                    (not cfg.cond['first']    or (cfg.cond['first']    and     self.bof_in)) and
                    (not cfg.cond['notfirst'] or (cfg.cond['notfirst'] and not self.bof_in))):
                    log.debug('Adding using vector-vector ALU')
                    self.v_out_d1 = self.vrf[cfg.addr*N:cfg.addr*N+N] + self.v_in
                else:
                    self.v_out_d1 = self.v_in


            if cfg.cache:
                self.vrf[cfg.cache_addr*N:cfg.cache_addr*N+N] = self.v_out_d1 
            
            self.v_in, self.eof_in, self.bof_in, self.chainId_in = copy(input_value)
            return self.v_out, self.eof_out, self.bof_out, self.chainId_out

    # Packs data efficiently
    class DataPacker():
        def __init__(self,N,M):
            self.v_in=np.zeros(N)
            self.v_out=np.zeros(N)
            self.eof_in = False
            self.bof_in = True
            self.chainId_in = 0
            self.v_out_valid=0
            self.v_out_size=0
            self.config=None

        def step(self,input_value):
            cfg=self.config[self.chainId_in]
            if (cfg.commit and 
                (not cfg.cond['last']     or (cfg.cond['last']     and     self.eof_in)) and
                (not cfg.cond['notlast']  or (cfg.cond['notlast']  and not self.eof_in)) and
                (not cfg.cond['first']    or (cfg.cond['first']    and     self.bof_in)) and
                (not cfg.cond['notfirst'] or (cfg.cond['notfirst'] and not self.bof_in))):
                if self.v_out_size==0:
                    self.v_out = self.v_in[:cfg.size]
                else:
                    self.v_out = np.append(self.v_out,self.v_in[:cfg.size])
                self.v_out_size=self.v_out_size+cfg.size
                if self.v_out_size==N:
                    log.debug('Data Packer full. Pushing values to Trace Buffer')
                    self.v_out_valid=1
                    self.v_out_size = 0
                else:
                    self.v_out_valid=0
            else:
                self.v_out_valid=0
            self.v_in, self.eof_in, self.bof_in, self.chainId_in = copy(input_value)
            return self.v_out, self.v_out_valid

    # Packs data efficiently
    class TraceBuffer():
        def __init__(self,N,TB_SIZE):
            self.input=np.zeros(N)
            self.mem=np.zeros((TB_SIZE,N))
            self.size=0

        def step(self,packed_data):
            output, output_valid = packed_data
            if output_valid:
                if self.size==TB_SIZE-1:
                    self.size=0
                self.mem[self.size]=output
                self.size=self.size+1
            self.input=copy(packed_data)
            

    def __init__(self,N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE):
        self.ib   = self.InputBuffer(N,IB_DEPTH)
        self.fu   = self.FilterUnit(N,M,FUVRF_SIZE)
        self.mvru = self.MatrixVectorReduce(N,M)
        self.vsru = self.VectorScalarReduce(N)
        self.vvalu= self.VectorVectorALU(N,VVVRF_SIZE)
        self.dp   = self.DataPacker(N,M)
        self.tb   = self.TraceBuffer(N,TB_SIZE)
        self.config()

    def step(self):
        log.debug('New step')
        chain = self.ib.step()
        chain = self.fu.step(chain)
        chain = self.mvru.step(chain)
        chain = self.vsru.step(chain)
        chain = self.vvalu.step(chain)
        packed_data = self.dp.step(chain)
        self.tb.step(packed_data)

    def config(self,fw=[]):
        #Configure processor
        self.ib.config=struct(num_chains=len(fw)+1)
        self.fu.config=[struct(filter=0,addr=0)]
        self.mvru.config=[struct(axis=0)]
        self.vsru.config=[struct(op=0)]
        self.vvalu.config=[struct(op=0,addr=0,cache=0,cache_addr=0)]
        self.dp.config=[struct(commit=0,size=0,cond={'last':False,'notlast':False,'first':False,'notfirst':False})]
        for idx, chain_instrs in enumerate(fw):
            self.fu.config.append(chain_instrs[0])
            self.mvru.config.append(chain_instrs[1])
            self.vsru.config.append(chain_instrs[2])
            self.vvalu.config.append(chain_instrs[3])
            self.dp.config.append(chain_instrs[4])

    def run(self):
        # Keep stepping through the circuit as long as we have instructions to execute
        for i in range(50):
            self.step()
        return self.tb.mem

# Hardware configurations (that can be done by VLIW instruction)
class compiler():
    # ISA
    def begin_chain(self):
        self.fu, self.mvru, self.vsru, self.vvalu, self.dp = copy(self.pass_through)
    def vv_filter(self,addr):
        self.fu.filter=1
        self.fu.addr=addr
    def m_reduce(self,axis='N'):
        if axis=='N':
            self.mvru.axis=1
        elif axis=='M':
            self.mvru.axis=2
        else:
            assert False, "Unknown axis for instruction m_reduce"
    def v_reduce(self):
        self.vsru.op=1
    def vv_add(self,addr,condition=None):
        self.vvalu.op=1
        self.vvalu.addr=addr
        if condition=="last" or condition=="notlast" or condition=="first" or condition=="notfirst" or condition is None:
            self.vvalu.cond[condition]=True
        else:
            assert False, "Condition not understood"
    def v_cache(self,cache_addr):
        self.vvalu.cache=1
        self.vvalu.cache_addr=cache_addr
    def v_commit(self,size=N,condition=None):
        self.dp.commit=1
        if size==N or size==M or size==1:
            self.dp.size=size
        else:
            assert False, "Cannot commit "+str(size)+" elements"
        if condition=="last" or condition=="notlast" or condition=="first" or condition=="notfirst" or condition is None:
            self.dp.cond[condition]=True
        else:
            assert False, "Condition not understood"
    def end_chain(self):
        self.firmware.append(copy([self.fu,self.mvru,self.vsru,self.vvalu,self.dp]))
    def compile(self):
        return self.firmware

    def __init__(self):
        self.firmware = []
        no_cond={'last':False,'notlast':False,'first':False,'notfirst':False}
        self.pass_through = [struct(filter=0,addr=0),struct(axis=0),struct(op=0),struct(op=0,addr=0,cond=copy(no_cond),cache=0,cache_addr=0),struct(commit=0,size=0,cond=copy(no_cond))]
        self.fu, self.mvru, self.vsru, self.vvalu, self.dp = self.pass_through[:]

def testSimpleDistribution():
    
    # Instantiate processor
    proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)

    # Initial hardware setup
    proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf

    # Firmware for a generic distribution
    def distribution(bins):
        assert bins%M==0, "Number of bins must be divisible by M for now"
        cp = compiler()
        for i in range(bins/M):
            cp.begin_chain()
            cp.vv_filter(i)
            cp.m_reduce(axis='M')
            cp.vv_add(i)
            cp.v_commit(M)
            cp.end_chain()
        return cp.compile()

    fw = distribution(2*M)

    # Feed one value to input buffer
    np.random.seed(42)
    input_vector = np.random.rand(N)*8
    proc.ib.push([input_vector,False])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.allclose(tb[0],[ 1.,2.,1.,0.,1.,1.,1.,1.]), "Test with distribution failed"
    print("Passed test #1")

testSimpleDistribution()

def testDualDistribution():

    # Instantiate processor
    proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)

    # Initial hardware setup
    proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf

    # Firmware for a distribution with 2 sets of N values
    def distribution(bins):
        assert bins%M==0, "Number of bins must be divisible by M for now"
        cp = compiler()
        for i in range(bins/M):
            cp.begin_chain()
            cp.vv_filter(i)
            cp.m_reduce('M')
            cp.vv_add(i,'notfirst')
            cp.v_cache(i)
            cp.v_commit(M,'last')
            cp.end_chain()
        return cp.compile()

    fw = distribution(2*M)

    # Feed one value to input buffer
    np.random.seed(42)
    input_vector1=np.random.rand(N)*8
    input_vector2=np.random.rand(N)*8

    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.allclose(tb[0],[ 2.,5.,1.,0.,2.,2.,2.,2.]), "Test with dual distribution failed"
    print("Passed test #2")

testDualDistribution()

def testSummaryStats():

    # Instantiate processor
    proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)
    cp = compiler()

    proc.fu.vrf=list(np.concatenate(([0.,float('inf')],list(reversed(range(FUVRF_SIZE*M-2)))))) # Initializing fuvrf for sparsity


    # Firmware for a distribution with 2 sets of N values
    def summaryStats():
        
        # Sum of all values
        cp.begin_chain()
        cp.v_reduce()
        cp.vv_add(0,'notfirst')
        cp.v_cache(0)
        cp.v_commit(1,'last')
        cp.end_chain()

        # Average sparsity
        cp.begin_chain()
        cp.vv_filter(0)
        cp.m_reduce('N')
        cp.v_reduce()
        cp.vv_add(1,'notfirst')
        cp.v_cache(1)
        cp.v_commit(1,'last')
        cp.end_chain()
        return cp.compile()

    fw = summaryStats()

    # Feed one value to input buffer
    np.random.seed(0)
    input_vector1=np.random.rand(N)*8-4
    input_vector2=np.random.rand(N)*8-4

    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.isclose(proc.dp.v_out[0],np.sum(input_vector1)*7+np.sum(input_vector2)), "Reduce sum failed"
    assert 47==int(proc.dp.v_out[1]), "Sparsity sum failed"
    print("Passed test #3")

testSummaryStats()