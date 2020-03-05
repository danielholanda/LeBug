import logging as log
import sys
import numpy as np

# Setting Debug level (can be debug, info, warning, error and critical)
log.basicConfig(stream=sys.stderr, level=log.DEBUG)

''' Emulation settings '''
DEBUG=True

''' Parameters of processor '''
# Input vector width
N = 8

# Number of range filters in filter unit
M = 2

# Input buffer depth
IB_DEPTH = 4

# Size of FUVRF
FUVRF_SIZE=64

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

        	# 
        	for i in range(M):
        		low_range = self.vrf[self.addr+i]
        		high_range = self.vrf[self.addr+i+1]
        		within_range = np.all([self.input>low_range, self.input<=high_range],axis=0)
        		self.output[i]=within_range[:]

        	print(self.output)	
        	#self.output=tmp_output
        	self.input=input_value
        	return self.output

    def __init__(self,N,M,IB_DEPTH,FUVRF_SIZE):
        self.ib = self.InputBuffer(N,IB_DEPTH)
        self.fu = self.FilterUnit(N,M,FUVRF_SIZE)

    def step(self):
    	chain = self.ib.step()
    	self.fu.step(chain)


# Instantiate processor
proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE)

# Initial hardware setup
proc.fu.vrf=list(range(FUVRF_SIZE)) # Initializing fuvrf

# Hardware configurations (that can be done by VLIW instruction)
proc.fu.addr=0

# Feed one value to input buffer
input_vector = np.random.rand(N)*10
proc.ib.push(input_vector)

# Step through it until we get the result
for i in range(3):
    proc.step()
    print(proc.fu.output)
    print("\n")