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
    
    def generateRtl(self,rtl):

        # Create subfolder where all files will be generated
        rtl_folder=os.getcwd()+"/rtl"
        if os.path.isdir(rtl_folder):
            shutil.rmtree(rtl_folder)

        # Copy all rtl blocks to folder
        #def copyRtlFile(file_name):
        #    copyfile(self.hwFolder+"/"+file_name, rtl_folder+"/"+file_name)
        #copyRtlFile("inputBuffer.sv")
        shutil.copytree(self.hwFolder+"/buildingBlocks", rtl_folder)

        # Connect all blocks in the processor
        f = open(rtl_folder+"/debugProcessor.sv", "w")
        for l in rtl:
            f.write(l+"\n")
        f.close()

    def __init__(self,N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE):
        ''' Verifying parameters '''
        assert math.log(N, 2).is_integer(), "N must be a power of 2" 
        assert math.log(M, 2).is_integer(), "N must be a power of 2" 
        assert M<=N, "M must be less or equal to N" 

        self.hwFolder = os.path.dirname(os.path.realpath(__file__))
        self.generateRtl(["empty","fgawga"])