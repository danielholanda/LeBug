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

    # This class describes an instantiated rtlModule
    class rtlInstance():
        def __init__(self,module_class,instance_name):
            self.module_class = module_class
            self.name = instance_name

    # This class describes an RTL module
    class rtlModule():

        # All include files go here
        def include(self,file):
            self.includes.append(file)

        def addInput(self,i):
            self.input=self.input+i

        # Recursively adds Modules to module
        def declareModule(self,dm_name):
            if self.included==False:
                self.dm.__dict__[dm_name]=self.parent.rtlModule(self,dm_name)
            else:
                print("Can't declare Modules on imported modules")

        # Lets us know about Modules that have been imported 
        def includeModule(self,dm_name):
            self.declareModule(dm_name)
            self.dm.__dict__[dm_name].included=True

        # Instantiate a given module
        def instantiateModule(self,module_class,instance_name):
            self.im.__dict__[instance_name]=self.parent.rtlInstance(module_class,instance_name)


        # Dump RTL class into readable RTL
        def dump(self):

            # Append with identation
            ident=self.getDepth()*"    "
            rtlCode=[]
            def apd(t):
                rtlCode.append(ident+t)
            
            # Add includes
            if self.includes!=[]:
                for i in self.includes:
                    apd('`include "'+i+'"')
                apd('')

            # Add declared module
            if self.input+self.output!=[]:
                apd('module  '+self.name+' (')
                # Add inputs and outputs
                for i in self.input:
                    bits= ' ['+str(i[2]-1)+':0]' if i[2]!=1 else ''
                    comma = ',' if i!=self.input[-1] else ''
                    apd('  input '+i[1]+' '+i[0]+bits+comma)
                for i in self.output:
                    bits= ' ['+str(i[2]-1)+':0]' if i[2]!=1 else ''
                    comma = ',' if i!=self.input[-1] else ''
                    apd('  output '+i[1]+' '+i[0]+bits+comma)
                apd(');')



                # Do recursive dumps for subclasses
                for m in self.dm.__dict__.keys():
                    mod=self.dm.__dict__[m]
                    if mod.included==False:
                        rtlCode=rtlCode+mod.dump()
                apd('endmodule')

            else:
                print(self.name+" has no inputs/outputs")
        
            return rtlCode 

        # Get depth of instantiated module
        def getDepth(self,d=0):
            if self.parent.__class__.__name__!="rtlHw":
                d=self.parent.getDepth(d)+1
            return d

        # Initializes the RTL file class
        def __init__(self,parent,name):
            self.name=name
            self.parent = parent        # name of Module
            self.includes=[]            # Stores include files
            self.wires=[]               # Stores wires
            self.regs=[]                # Stores regs
            self.input=[]               # Store all inputs logic ports
            self.output=[]              # Store all outputs logic ports
            self.included=False         # Is true if the module has been imported
            self.dm=struct()            # Those are the declare modules
            self.im=struct()            # Those are the instantiated modules

    def rtlLogic(self):
        # Create RTL using custom RTL class
        rtl = self.rtlModule(self,"debugger")
        rtl.addInput([['clk','logic',1],['valid','logic',1],['vector','logic',self.N]])

        # Adds includes to the beginning of the file
        rtl.include("inputBuffer.sv")

        # Tells the class about the included modules
        rtl.includeModule("inputBuffer")
        rtl.dm.inputBuffer.addInput([['clk','logic',1],['vector','logic',self.N]])

        # Instantiate module
        rtl.instantiateModule(rtl.dm.inputBuffer,"ib")
        #rtl.im.ib.connectInputs(rtl.input)

        # Declaring a Module
        rtl.declareModule("testbench")
        rtl.dm.testbench.addInput([['clk','logic',1],['vector','logic',self.N]])

        rtl.declareModule("Module2")

        return rtl.dump()

    def generateRtl(self):

        # Create subfolder where all files will be generated
        rtl_folder=os.getcwd()+"/rtl"
        if os.path.isdir(rtl_folder):
            shutil.rmtree(rtl_folder)
        shutil.copytree(self.hwFolder+"/buildingBlocks", rtl_folder)

        # Writes to file
        f = open(rtl_folder+"/debugProcessor.sv", "w")
        for l in self.rtlLogic():
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
        