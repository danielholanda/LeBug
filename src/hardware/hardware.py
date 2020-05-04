import logging as log
import sys, math, os, shutil
import numpy as np
from copy import deepcopy as copy

# Setting Debug level (can be debug, info, warning, error and critical)
log.basicConfig(stream=sys.stderr, level=log.INFO)

''' General settings '''
DEBUG=True

''' Useful functions '''
class struct:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    def __repr__(self):
        return str(self.__dict__)

class rtlHw():
    
    # This is a python class that holds RTL code
    class rtlModule():

        # All include files go here
        def include(self,file):
            self.includes.append(file)

        # Recursively adds submodules to module
        def addSubmodule(self,sm_name,inputLogic=[],outputLogic=[]):
            self.sm.__dict__[sm_name]=self.parent.rtlModule(self,inputLogic,outputLogic)

        # Dump RTL class into readable RTL
        def dump(self):
            rtl=[]
            for i in self.includes:
                rtl.append('`include "'+i+'"')

            # Continue here
            for i in self.inputLogic:
                rtl.append('still need to add input logic '+i[0])

            for i in self.outputLogic:
                rtl.append('still need to add outputLogic logic '+i[0])

            # Do recursive dumps for subclasses
            for m in self.sm.__dict__.keys():
                rtl=rtl+self.sm.__dict__[m].dump()
            return rtl

        # Initializes the RTL file class
        def __init__(self,parent,inputLogic=[],outputLogic=[]):
            self.parent = parent
            self.includes=[]            # Stores include files
            self.wires=[]               # Stores wires
            self.regs=[]                # Stores regs
            self.inputLogic=inputLogic  # Store all input logic ports
            self.outputLogic=outputLogic# Store all output logic ports
            self.sm=struct()            # All submodules go here

    def generateRtl(self):

        # Create subfolder where all files will be generated
        rtl_folder=os.getcwd()+"/rtl"
        if os.path.isdir(rtl_folder):
            shutil.rmtree(rtl_folder)
        shutil.copytree(self.hwFolder+"/buildingBlocks", rtl_folder)

        # Create RTL using custom RTL class
        rtl = self.rtlModule(self)

        # Includes all needed files
        rtl.include("inputBuffer.sv")

        il=[['clk',1],['vector',self.N]]        
        rtl.addSubmodule("main",inputLogic=il)

        # Writes to file
        f = open(rtl_folder+"/debugProcessor.sv", "w")
        print(rtl.dump())
        for l in rtl.dump():
            f.write(l+"\n")
        f.close()

    def __init__(self,N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE):
        ''' Verifying parameters '''
        assert math.log(N, 2).is_integer(), "N must be a power of 2" 
        assert math.log(M, 2).is_integer(), "N must be a power of 2" 
        assert M<=N, "M must be less or equal to N" 

        self.N=N
        self.M=M
        self.hwFolder = os.path.dirname(os.path.realpath(__file__))
        self.generateRtl()
        