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
    class rtlFile():

        # All include files go here
        def include(self,file):
            self.includes.append(file)

        # Dump RTL class into readable RTL
        def dump(self):
            rtl=[]
            for i in self.includes:
                rtl.append('`include "'+i+'"')
            return rtl

        # Initializes the RTL file class
        def __init__(self):
            self.includes=[]

    def generateRtl(self):

        # Create subfolder where all files will be generated
        rtl_folder=os.getcwd()+"/rtl"
        if os.path.isdir(rtl_folder):
            shutil.rmtree(rtl_folder)
        shutil.copytree(self.hwFolder+"/buildingBlocks", rtl_folder)

        # Includes all needed files
        self.rtl.include("inputBuffer.sv")

        # Writes to file
        f = open(rtl_folder+"/debugProcessor.sv", "w")
        for l in self.rtl.dump():
            f.write(l+"\n")
        f.close()

    def __init__(self,N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE):
        ''' Verifying parameters '''
        assert math.log(N, 2).is_integer(), "N must be a power of 2" 
        assert math.log(M, 2).is_integer(), "N must be a power of 2" 
        assert M<=N, "M must be less or equal to N" 

        self.hwFolder = os.path.dirname(os.path.realpath(__file__))
        self.rtl = self.rtlFile()

        self.generateRtl()