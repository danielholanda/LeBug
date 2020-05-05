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

        # Create dict connection a module instance to signals
        def mapPorts(self,module_ports,signals_to_connect):
            # Ports are properly mapped if they have the same size and aproximately the same name
            portMap={}
            for i in module_ports:
                for j in signals_to_connect:
                    if i.bits==j.bits and (i.name==j.name or i.name==j.name[j.name.find("_")+1:]):
                        portMap[i.name]=j.name 
            assert len(portMap.keys())==len(self.module_input), "Port map failed"
            return portMap

        # Connect inputs of instance
        def connectInputs(self,signals_to_connect):
            
            # Add clock to signals to connect if not there
            clock_found=False
            for i in signals_to_connect:
                if i.name=='clk':
                    clock_found=True
            if not clock_found:
                signals_to_connect.append(struct(name='clk',type='logic',bits=1))

            # Check if number of signals is the same
            assert len(signals_to_connect)==len(self.module_input), "Not the same number of connected signals"

            # Map ports
            self.instance_input=self.mapPorts(self.module_input,signals_to_connect)


        def __init__(self,module_class,instance_name):
            self.module_class = module_class
            self.name = instance_name
            self.module_input=module_class.input
            self.module_output=module_class.output
            self.instance_input={}
            self.instance_output={}

            # Map outputs using the name of the instance
            for o in module_class.output:
               self.instance_output[o]= self.name+"_"+o.name

    # This class describes an RTL module
    class rtlModule():

        # All include files go here
        def include(self,file):
            self.includes.append(file)

        def addInput(self,inputs):
            for i in inputs:
                self.input.append(struct(name=i[0],type=i[1],bits=i[2]))

        def addOutput(self,outputs):
            for o in outputs:
                self.output.append(struct(name=o[0],type=o[1],bits=o[2]))

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

            # Append with identation (apdi is apd shifted)
            ident=self.getDepth()*"    "
            rtlCode=[]
            def apd(t):
                rtlCode.append(ident+t)
            def apdi(t):
                rtlCode.append(ident+"    "+t)
            
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
                    bits= ' ['+str(i.bits-1)+':0]' if i.bits>1 else ''
                    comma = ',' if i!=self.input[-1] else ''
                    apd('  input '+i.type+' '+i.name+bits+comma)
                for i in self.output:
                    bits= ' ['+str(i.bits-1)+':0]' if i.bits>1 else ''
                    comma = ',' if i!=self.input[-1] else ''
                    apd('  output '+i.type+' '+i.name+bits+comma)
                apd(');')


                # Do recursive dumps for submodules declared in this module
                for m in self.dm.__dict__.keys():
                    mod=self.dm.__dict__[m]
                    if mod.included==False:
                        rtlCode=rtlCode+mod.dump()
                
                # Instantiated modules
                for i in self.im.__dict__.keys():
                    inst=self.im.__dict__[i]
                    apdi('')
                    # Declare outputs
                    for out in inst.instance_output:
                        bits= ' ['+str(out.bits-1)+':0]' if out.bits>1 else ''
                        apdi("output "+out.type+" "+out.name+bits+";")
                    # Instantiate and connect module
                    apdi(inst.module_class.name+" "+inst.name+"();")

                # Finish module
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
        rtl.dm.inputBuffer.addInput([['clk','logic',1],['valid','logic',1],['vector','logic',self.N]])
        rtl.dm.inputBuffer.addOutput([['valid','logic',1],['vector','logic',self.N]])

        # Instantiate module
        rtl.instantiateModule(rtl.dm.inputBuffer,"ib")
        rtl.im.ib.connectInputs(rtl.input)

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
        