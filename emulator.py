import logging as log
import sys, math
import numpy as np
from copy import deepcopy as copy

# Setting Debug level (can be debug, info, warning, error and critical)
log.basicConfig(stream=sys.stderr, level=log.INFO)
np.random.seed(42)

''' Emulation settings '''
DEBUG=True

''' Parameters of processor '''
# Input vector width
N = 8

# Number of range filters in filter unit
M = 4 

# Input buffer depth
IB_DEPTH = 4

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

        def push(self,pushed_vals):
            v_in, eof_in = pushed_vals
            assert list(v_in.shape)==[N], "Input must be Nx1"
            assert len(self.buffer)<=self.size, "Input buffer overflowed"
            log.debug('Vector inserted into input buffer\n'+str(v_in))
            self.buffer.append([v_in,eof_in])

        def pop(self):
            assert len(self.buffer)>0, "Input buffer is empty"
            return self.buffer.pop(-1)

        def step(self):
            v_out, eof_out = self.buffer[-1]
            return v_out, eof_out

    # Filter Unit
    class FilterUnit():
        def __init__(self,N,M,FUVRF_SIZE):
            self.v_in=np.zeros(N)
            self.m_out=np.zeros((M,N))
            self.eof_in = False
            self.eof_out = False
            self.vrf=np.zeros(FUVRF_SIZE*M)
            self.config=struct(filter=0,addr=0)

        def step(self,input_value):
            # Check if the vector is within M ranges
            log.debug('Filter input:'+str(self.v_in))
            log.debug('Filtering using the following ranges:'+str(self.vrf[self.config.addr*M:self.config.addr*M+M+1]))
            if self.config.filter==1:
                for i in range(M):
                    low_range = self.vrf[self.config.addr*M+i]
                    high_range = self.vrf[self.config.addr*M+i+1]
                    within_range = np.all([self.v_in>low_range, self.v_in<=high_range],axis=0)
                    self.m_out[i]=within_range[:]
            # If we are not filtering, just pass the value through 
            else:
                for i in range(M):
                    self.m_out[i] = self.v_in if i==0 else np.zeros(N)

            self.eof_out = copy(self.eof_in)
            self.v_in, self.eof_in = copy(input_value)
            return self.m_out, self.eof_out

    # This block will reduce the matrix along a given axis
    # If M<N, then the results will be padded with zeros
    class MatrixVectorReduce():
        def __init__(self,N,M):
            self.m_in=np.zeros((M,N))
            self.v_out=np.zeros(N)
            self.eof_in = False
            self.eof_out = False
            self.config=struct(axis=0)

        def step(self,input_value):
            # Reduce matrix along a given axis
            if self.config.axis==0:
                log.debug('Passing first vector through reduce unit')
                self.v_out=self.m_in[0]
            elif self.config.axis==1:
                log.debug('Reducing matrix along N axis (axis = '+str(self.config.axis)+')')
                self.v_out=np.sum(self.m_in,axis=0)
            elif self.config.axis==2:
                log.debug('Reducing matrix along M axis (axis = '+str(self.config.axis)+')')
                self.v_out=np.sum(self.m_in,axis=1)
                if N!=M:
                    log.debug('Padding results with '+str(N-M)+' zeros')
                    self.v_out=np.concatenate((self.v_out,np.zeros(N-M)))

            self.eof_out = copy(self.eof_in)
            self.m_in, self.eof_in = copy(input_value)
            return self.v_out, self.eof_out

    # This block will reduce the matrix along a given axis
    class VectorVectorALU():
        def __init__(self,N,VVVRF_SIZE):
            self.v_in=np.zeros(N)
            self.v_out=np.zeros(N)
            self.eof_in = False
            self.eof_out = False
            self.vrf=np.zeros(N*VVVRF_SIZE)
            self.config=struct(op=0,addr=0,cache=0,cache_addr=0)
            self.delay1=np.zeros(N)
            self.delay2=np.zeros(N)

        def step(self,input_value):
            # Delay for 2 cycles, so this FU takes 3 cycles (read, calculate, write)
            self.v_out = self.delay2
            self.delay2 = self.delay1
            if self.config.op==0:
                log.debug('ALU is passing values through')
                self.delay1 = self.v_in
            elif self.config.op==1:
                log.debug('Adding using vector-vector ALU')
                self.delay1 = self.vrf[self.config.addr*N:self.config.addr*N+N] + self.v_in
            elif self.config.op==2:
                log.debug('Storing values in VVALU_VRF and passing through')
                self.delay1 = self.v_in
            if self.config.cache:
                self.vrf[self.config.cache_addr*N:self.config.cache_addr*N+N] = self.delay1 
            
            self.eof_out = copy(self.eof_in)
            self.v_in, self.eof_in = copy(input_value)
            return self.v_out, self.eof_out

    # Packs data efficiently
    class DataPacker():
        def __init__(self,N,M):
            self.v_in=np.zeros(N)
            self.v_out=np.zeros(N)
            self.eof_in = False
            self.v_out_valid=0
            self.v_out_size=0
            self.config=struct(commit=0,size=0)

        def step(self,input_value):
            if self.config.commit:
                if self.v_out_size==0:
                    self.v_out = self.v_in[:self.config.size]
                else:
                    self.v_out = np.append(self.v_out,self.v_in[:self.config.size])
                self.v_out_size=self.v_out_size+self.config.size
                if self.v_out_size==N:
                    log.debug('Data Packer full. Pushing values to Trace Buffer')
                    self.v_out_valid=1
                else:
                    self.v_out_valid=0
            else:
                self.v_out_valid=0
            
            self.v_in, self.eof_in = copy(input_value)
            
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
        self.vvalu= self.VectorVectorALU(N,VVVRF_SIZE)
        self.dp   = self.DataPacker(N,M)
        self.tb   = self.TraceBuffer(N,TB_SIZE)

    def step(self):
        log.debug('New step')
        chain = self.ib.step()
        chain = self.fu.step(chain)
        chain = self.mvru.step(chain)
        chain = self.vvalu.step(chain)
        packed_data = self.dp.step(chain)
        self.tb.step(packed_data)

    def run(self,compiled_firmware):
        for idx, instr in enumerate(compiled_firmware):
            # Dispatch Instructions to each functional unit
            self.fu.config ,self.mvru.config, self.vvalu.config, self.dp.config = instr
            # Keep stepping through the circuit as long as we have instructions to execute
            self.step()
        return self.tb.mem



# Instantiate processor
proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)

# Initial hardware setup
proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf

# Hardware configurations (that can be done by VLIW instruction)
class compiler():
    # ISA
    def begin_chain(self):
        self.fu, self.mvru, self.vvalu, self.dp = copy(self.pass_through)
    def filter(self,addr):
        self.fu.filter=1
        self.fu.addr=addr
    def reduceN(self):
        self.mvru.axis=1
    def reduceM(self):
        self.mvru.axis=2
    def vv_add_new(self,addr):
        self.vvalu.op=2
        self.addr=addr
    def vv_add(self,addr):
        self.vvalu.op=1
        self.vvalu.addr=addr
    def v_cache(self,cache_addr):
        self.vvalu.cache=1
        self.vvalu.cache_addr=cache_addr
    def commitM(self):
        self.dp.commit=1
        self.dp.size=M
    def commitN(self):
        self.dp.commit=1
        self.dp.size=N
    def commit1(self):
        self.dp.commit=1
        self.dp.size=1
    def end_chain(self):
        self.firmware.append(copy([self.fu,self.mvru,self.vvalu,self.dp]))
    def compile(self):
        # We will compile to abstract away the idea of cycles
        # Input: List of operations each chain needs to perform
        # Output: For each cycle, which operation each function unit should perform
        compiled_firmware=[]
        pipeline_depth=7
        number_of_chains=len(self.firmware)
        for i in range(pipeline_depth+number_of_chains-1):
            chain_instrs = self.pass_through[:]
            # For the FU, which takes 1 cycle
            if i<number_of_chains:
                    chain_instrs[0]=self.firmware[i][0]
            # For the MVRU, which takes 1 cycle
            if i<number_of_chains+1 and i>0:
                    chain_instrs[1]=self.firmware[i-1][1]
            # For the VVALU, which takes 3 cycles
            if i<number_of_chains+2 and i>1:
                    chain_instrs[2]=self.firmware[i-2][2]
            # For the Data Packer, which takes 1 cycle
            if i<number_of_chains+5 and i>4:
                    chain_instrs[3]=self.firmware[i-5][3]
            # There is one more cycle for writing the data in the trace buffer

            compiled_firmware.append(chain_instrs)
        return compiled_firmware

    def __init__(self):
        self.firmware = []
        self.pass_through = [struct(filter=0,addr=0),struct(axis=0),struct(op=0,addr=0,cache=0,cache_addr=0),struct(commit=0,size=0)]
        self.fu, self.mvru, self.vvalu, self.dp = self.pass_through[:]

def testSimpleDistribution():
    # Firmware for a generic distribution
    def distribution(bins):
        assert bins%M==0, "Number of bins must be divisible by M for now"
        cp = compiler()
        for i in range(bins/M):
            cp.begin_chain()
            cp.filter(i)
            cp.reduceM()
            cp.vv_add(i)
            cp.commitM()
            cp.end_chain()
        return cp.compile()

    compiled_firmware = distribution(2*M)

    # Printing sequence of instructions that will be executed at each cycle
    print("\nSequence of operations per cycle:")
    for idx, chain_instr in enumerate(compiled_firmware):
        print("\tCycle #"+str(idx)+" "+str(chain_instr))

    # Feed one value to input buffer
    input_vector = np.random.rand(N)*8
    proc.ib.push([input_vector,False])
    proc.step()

    # Step through it until we get the result
    tb = proc.run(compiled_firmware)
    assert np.allclose(tb[0],[ 1.,2.,1.,0.,1.,1.,1.,1.]), "Test with distribution failed"

testSimpleDistribution()

def testDualDistribution():
    # Firmware for a distribution with 2 sets of N values
    def distribution(bins):
        assert bins%M==0, "Number of bins must be divisible by M for now"
        cp = compiler()
        for i in range(bins/M):
            cp.begin_chain()
            cp.filter(i)
            cp.reduceM()
            cp.vv_add(i)
            cp.v_cache(i)
            cp.commitM('eof')
            cp.end_chain()
        return cp.compile()

    compiled_firmware = distribution(2*M)

    # Printing sequence of instructions that will be executed at each cycle
    print("\nSequence of operations per cycle:")
    for idx, chain_instr in enumerate(compiled_firmware):
        print("\tCycle #"+str(idx)+" "+str(chain_instr))

    # Feed one value to input buffer
    proc.ib.push(np.random.rand(N)*8)
    proc.ib.push(np.random.rand(N)*8)
    proc.step()

    # Step through it until we get the result
    tb = proc.run(compiled_firmware)
    assert np.allclose(tb[0],[ 1.,2.,1.,0.,1.,1.,1.,1.]), "Test with distribution failed"