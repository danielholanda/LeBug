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

        def addInputLogic(self,il):
            self.inputLogic=self.inputLogic+il

        # Recursively adds submodules to module
        def declareSubmodule(self,dm_name):
            if self.included==False:
                self.dm.__dict__[dm_name]=self.parent.rtlModule(self,dm_name)
            else:
                print("Can't declare submodules on imported modules")

        # Lets us know about submodules that have been imported 
        def includeSubmodule(self,dm_name):
            self.declareSubmodule(dm_name)
            self.dm.__dict__[dm_name].included=True


        # Dump RTL class into readable RTL
        def dump(self):

            # Append with identation
            ident=self.getDepth()*"    "
            rtl=[]
            def apd(t):
                rtl.append(ident+t)
            
            # Add includes
            for i in self.includes:
                apd('`include "'+i+'"')


            # Instantiate module if inputs are available
            if self.inputLogic+self.outputLogic!=[]:
                apd('module  '+self.name+' (')
                # Add inputs
                for i in self.inputLogic:
                    apd('still need to add input logic '+i[0])

                for i in self.outputLogic:
                    apd('still need to add outputLogic logic '+i[0])

                # Do recursive dumps for subclasses
                for m in self.dm.__dict__.keys():
                    mod=self.dm.__dict__[m]
                    if mod.included==False:
                        rtl=rtl+mod.dump()
                apd('endmodule')

            else:
                print(self.name+" has no inputs/outputs")
        
            return rtl 

        # Get depth of instantiated module
        def getDepth(self,d=0):
            if self.parent.__class__.__name__!="rtlHw":
                d=self.parent.getDepth(d)+1
            return d

        # Initializes the RTL file class
        def __init__(self,parent,name):
            self.name=name
            self.parent = parent        # name of submodule
            self.includes=[]            # Stores include files
            self.wires=[]               # Stores wires
            self.regs=[]                # Stores regs
            self.inputLogic=[]          # Store all input logic ports
            self.outputLogic=[]         # Store all output logic ports
            self.included=False         # Is true if the module has been imported
            self.dm=struct()            # Those are the declare modules
            self.im=struct()            # Those are the instantiated modules

    def rtlLogic(self):
        # Create RTL using custom RTL class
        rtl = self.rtlModule(self,"main")
        rtl.addInputLogic([['clk',1],['valid',1],['vector',self.N]])

        # Adds includes to the beginning of the file
        rtl.include("inputBuffer.sv")

        # Tells the class about the included modules
        rtl.includeSubmodule("inputBuffer")
        rtl.dm.inputBuffer.addInputLogic([['clk',1],['vector',self.N]])

        # Declaring a submodule
        rtl.declareSubmodule("testbench")
        rtl.dm.testbench.addInputLogic([['clk',1],['vector',self.N]])

        rtl.declareSubmodule("submodule2")

        return rtl

    def generateRtl(self):

        # Create subfolder where all files will be generated
        rtl_folder=os.getcwd()+"/rtl"
        if os.path.isdir(rtl_folder):
            shutil.rmtree(rtl_folder)
        shutil.copytree(self.hwFolder+"/buildingBlocks", rtl_folder)

        rtl=self.rtlLogic()

        # Writes to file
        f = open(rtl_folder+"/debugProcessor.sv", "w")
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
        