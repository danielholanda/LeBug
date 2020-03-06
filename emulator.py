import logging as log
import sys, math
import numpy as np
from copy import deepcopy as copy

# Setting Debug level (can be debug, info, warning, error and critical)
log.basicConfig(stream=sys.stderr, level=log.DEBUG)

''' Emulation settings '''
DEBUG=True

''' Parameters of processor '''
# Input vector width
N = 8

# Number of range filters in filter unit
M = 4 

# Input buffer depth
IB_DEPTH = 4

# Size of FUVRF
FUVRF_SIZE=64

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
            self.output=[]

        def push(self,v):
            assert list(v.shape)==[N], "Input must be Nx1"
            assert len(self.buffer)<=self.size, "Input buffer overflowed"
            log.debug('Vector inserted into input buffer\n'+str(v))
            self.buffer.append(list(v))

        def pop(self):
            assert len(self.buffer)>0, "Input buffer is empty"
            return self.buffer.pop(-1)

        def step(self):
            self.output = np.array(self.buffer[-1])
            return self.output

    # Filter Unit
    class FilterUnit():
        def __init__(self,N,M,FUVRF_SIZE):
            self.input=np.zeros(N)
            self.output=np.zeros((M,N))
            self.vrf=np.zeros(FUVRF_SIZE)
            self.config=struct(addr=0)

        def step(self,input_value):
            # Check if the vector is within M ranges
            log.debug('Filter input:'+str(self.input))
            log.debug('Filtering using the following ranges:'+str(self.vrf[self.config.addr:self.config.addr+M+1]))
            for i in range(M):
                low_range = self.vrf[self.config.addr+i]
                high_range = self.vrf[self.config.addr+i+1]
                within_range = np.all([self.input>low_range, self.input<=high_range],axis=0)
                self.output[i]=within_range[:]

            self.input=copy(input_value)
            return self.output

    # This block will reduce the matrix along a given axis
    # If M<N, then the results will be padded with zeros
    class MatrixVectorReduce():
        def __init__(self,N,M):
            self.input=np.zeros((M,N))
            self.output=np.zeros(N)
            self.config=struct(axis=0)

        def step(self,input_value):
            # Reduce matrix along a given axis
            self.output=np.sum(self.input,axis=self.config.axis)
            if self.config.axis==0:
                log.debug('Reducing matrix along N axis (axis = '+str(self.config.axis)+')')
            elif self.config.axis==1:
                log.debug('Reducing matrix along M axis (axis = '+str(self.config.axis)+')')
                if N!=M:
                    log.debug('Padding results with '+str(N-M)+' zeros')
                    self.output=np.concatenate((self.output,np.zeros(N-M)))

            self.input=copy(input_value)
            return self.output

    # This block will reduce the matrix along a given axis
    class VectorVectorALU():
        def __init__(self,N):
            self.input=np.zeros(N)
            self.output=np.zeros(N)
            self.config=struct(reset=0,op=0)

        def step(self,input_value):
            if self.config.reset:
                log.debug('Resetting vector-vector ALU output')
                self.output = np.zeros(N)
            if self.config.op==0:
                log.debug('Adding using vector-vector ALU')
                self.output = self.output + self.input
            self.input=copy(input_value)
            return self.output

    def __init__(self,N,M,IB_DEPTH,FUVRF_SIZE):
        self.ib   = self.InputBuffer(N,IB_DEPTH)
        self.fu   = self.FilterUnit(N,M,FUVRF_SIZE)
        self.mvru = self.MatrixVectorReduce(N,M)
        self.vvalu= self.VectorVectorALU(N)

    def step(self):
        log.debug('New step')
        chain = self.ib.step()
        chain = self.fu.step(chain)
        chain = self.mvru.step(chain)
        chain = self.vvalu.step(chain)
        print(self.fu.output)
        print(self.mvru.output)
        print(self.vvalu.output)

    def run(self,compiled_firmware):
        for idx, instr in enumerate(compiled_firmware):
            # Dispatch Instructions to each functional unit
            self.fu.config ,self.mvru.config, self.vvalu.config = instr
            # Keep stepping through the circuit as long as we have instructions to execute
            self.step()



# Instantiate processor
proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE)

# Initial hardware setup
proc.fu.vrf=list(range(FUVRF_SIZE)) # Initializing fuvrf

# Hardware configurations (that can be done by VLIW instruction)
class compiler():
    # ISA
    def begin_chain(self):
        self.fu, self.mvru, self.vvalu = copy(self.pass_through)
    def filter(self,addr):
        self.fu.addr=addr
    def reduceN(self):
        self.mvru.axis=0
    def reduceM(self):
        self.mvru.axis=1
    def vv_add_new(self):
        self.vvalu.reset=1
        self.vvalu.op=0
    def vv_add(self):
        self.vvalu.reset=0
        self.vvalu.op=0
    def end_chain(self):
        self.firmware.append(copy([self.fu,self.mvru,self.vvalu]))
    def compile(self):
        # We will compile to abstract away the idea of cycles
        # Input: List of operations each chain needs to perform
        # Output: For each cycle, which operation each function unit should perform
        compiled_firmware=[]
        pipeline_depth=3
        number_of_chains=len(self.firmware)
        for i in range(pipeline_depth+number_of_chains-1):
            chain_instrs = self.pass_through[:]
            for j in range(pipeline_depth):
                if i<number_of_chains+j and i>j-1:
                    chain_instrs[j]=self.firmware[i-j][j]
            compiled_firmware.append(chain_instrs)
        return compiled_firmware

    def __init__(self):
        self.firmware = []
        self.pass_through = [struct(addr=0),struct(axis=0),struct(reset=0,op=0)]
        self.fu, self.mvru, self.vvalu = self.pass_through[:]

# Firmware for a generic distribution
def distribution(bins):
    assert bins%M==0, "Number of bins must be divisible by M for now"
    cp = compiler()
    cp.begin_chain()
    cp.filter(0)
    cp.reduceM()
    cp.vv_add_new()
    cp.end_chain()
    for i in range(1,bins/M):
        cp.begin_chain()
        cp.filter(i*M)
        cp.reduceM()
        cp.vv_add()
        cp.end_chain()
    return cp.compile()

compiled_firmware = distribution(2*M)

# Printing sequence of instructions that will be executed at each cycle
print("\nSequence of operations per cycle:")
for idx, chain_instr in enumerate(compiled_firmware):
    print("\tCycle #"+str(idx)+" "+str(chain_instr))


# Feed one value to input buffer
input_vector = np.random.rand(N)*8
proc.ib.push(input_vector)
proc.step()

# Step through it until we get the result
proc.run(compiled_firmware)
#print(proc.fu.output)
#print(proc.mvru.output)
#print(proc.vvalu.output)
    