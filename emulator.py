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
IB_DEPTH = 4

# Size of FUVRF in M*elements
FUVRF_SIZE=4

# SIze of VVVRF in N*elements
VVVRF_SIZE=8

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
            self.vrf=np.zeros(FUVRF_SIZE*M)
            self.config=struct(addr=0)

        def step(self,input_value):
            # Check if the vector is within M ranges
            log.debug('Filter input:'+str(self.input))
            log.debug('Filtering using the following ranges:'+str(self.vrf[self.config.addr*M:self.config.addr*M+M+1]))
            for i in range(M):
                low_range = self.vrf[self.config.addr*M+i]
                high_range = self.vrf[self.config.addr*M+i+1]
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
        def __init__(self,N,VVVRF_SIZE):
            self.input=np.zeros(N)
            self.output=np.zeros(N)
            self.vrf=np.zeros(N*VVVRF_SIZE)
            self.config=struct(op=0,addr1=0,addr2=0)
            self.delay1=np.zeros(N)
            self.delay2=np.zeros(N)

        def step(self,input_value):
        	# Delay for 2 cycles, so this FU takes 3 cycles (read, calculate, write)
            self.output = self.delay2
            self.delay2 = self.delay1
            if self.config.op==0:
            	log.debug('ALU is passing values through')
            	self.delay1 = self.input
            elif self.config.op==1:
                log.debug('Adding using vector-vector ALU')
                self.delay1 = self.vrf[self.config.addr1*N:self.config.addr1*N+N] + self.input
                self.vrf[self.config.addr2*N:self.config.addr2*N+N] = self.delay1 
            elif self.config.op==2:
                log.debug('Storing values in VVALU_VRF and passing through')
                self.delay1 = self.input
                self.vrf[self.config.addr1*N:self.config.addr1*N+N] = self.delay1 
            self.input=copy(input_value)
            
            return self.output

    def __init__(self,N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE):
        self.ib   = self.InputBuffer(N,IB_DEPTH)
        self.fu   = self.FilterUnit(N,M,FUVRF_SIZE)
        self.mvru = self.MatrixVectorReduce(N,M)
        self.vvalu= self.VectorVectorALU(N,VVVRF_SIZE)

    def step(self):
        log.debug('New step')
        chain = self.ib.step()
        chain = self.fu.step(chain)
        chain = self.mvru.step(chain)
        chain = self.vvalu.step(chain)

    def run(self,compiled_firmware):
        for idx, instr in enumerate(compiled_firmware):
            # Dispatch Instructions to each functional unit
            self.fu.config ,self.mvru.config, self.vvalu.config = instr
            # Keep stepping through the circuit as long as we have instructions to execute
            self.step()



# Instantiate processor
proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)

# Initial hardware setup
proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf

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
    def vv_add_new(self,addr1):
        self.vvalu.op=2
        self.addr1=addr1
        self.addr2=None
    def vv_add(self,addr1,addr2):
        self.vvalu.op=1
        self.vvalu.addr1=addr1
        self.vvalu.addr2=addr2
    def end_chain(self):
        self.firmware.append(copy([self.fu,self.mvru,self.vvalu]))
    def compile(self):
        # We will compile to abstract away the idea of cycles
        # Input: List of operations each chain needs to perform
        # Output: For each cycle, which operation each function unit should perform
        compiled_firmware=[]
        pipeline_depth=5
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

            compiled_firmware.append(chain_instrs)
        return compiled_firmware

    def __init__(self):
        self.firmware = []
        self.pass_through = [struct(addr=0),struct(axis=0),struct(op=0,addr1=0,addr2=0)]
        self.fu, self.mvru, self.vvalu = self.pass_through[:]

# Firmware for a generic distribution
def distribution(bins):
    assert bins%M==0, "Number of bins must be divisible by M for now"
    cp = compiler()
    for i in range(bins/M):
        cp.begin_chain()
        cp.filter(i)
        cp.reduceM()
        cp.vv_add(i,i)
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

print("\nInputs:")
print(input_vector)
print("\nResults stored in VVALU VRF")
for i in [0,1]:
	print("\tRange: "+str(proc.fu.vrf[i*M:i*M+M+1]))
	print("\tDistribution: "+str(proc.vvalu.vrf[i*N:i*N+N][:M]))
