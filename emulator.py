import logging as log
import sys, math
import numpy as np

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
            self.addr=0

        def step(self,input_value):

            # Check if the vector is within M ranges
            log.debug('Filtering using the following ranges:'+str(self.vrf[self.addr:self.addr+M+1]))
            for i in range(M):
                low_range = self.vrf[self.addr+i]
                high_range = self.vrf[self.addr+i+1]
                within_range = np.all([self.input>low_range, self.input<=high_range],axis=0)
                self.output[i]=within_range[:]

            self.input=input_value
            return self.output

    # This block will reduce the matrix along a given axis
    # If M<N, then the results will be padded with zeros
    class MatrixVectorReduce():
        def __init__(self,N,M):
            self.input=np.zeros((M,N))
            self.output=np.zeros(N)
            self.axis=0

        def step(self,input_value):
            # Reduce matrix along a given axis
            self.output=np.sum(self.input,axis=self.axis)
            if self.axis==0:
                log.debug('Reducing matrix along N axis (axis = '+str(self.axis)+')')
            elif self.axis==1:
                log.debug('Reducing matrix along M axis (axis = '+str(self.axis)+')')
                if N!=M:
                    log.debug('Padding results with '+str(N-M)+' zeros')
                    self.output=np.concatenate((self.output,np.zeros(N-M)))

            self.input=input_value
            return self.output

    # This block will reduce the matrix along a given axis
    class VectorVectorALU():
        def __init__(self,N):
            self.input=np.zeros(N)
            self.output=np.zeros(N)
            self.op=0

        def step(self,input_value):
            if self.reset:
            	log.debug('Resetting vector-vector ALU output')
                self.output = np.zeros(N)
            if self.op==0:
                log.debug('Adding using vector-vector ALU')
                self.output = self.output + self.input
            self.input=input_value
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


# Instantiate processor
proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE)

# Initial hardware setup
proc.fu.vrf=list(range(FUVRF_SIZE)) # Initializing fuvrf

# Hardware configurations (that can be done by VLIW instruction)
proc.fu.addr=0
proc.mvru.axis=1
proc.vvalu.reset=0
proc.vvalu.op=0

# Feed one value to input buffer
input_vector = np.random.rand(N)*4
proc.ib.push(input_vector)

# Step through it until we get the result
for i in range(4):
    proc.step()
    print(proc.fu.output)
    print(proc.mvru.output)
    print(proc.vvalu.output)
    print("\n")