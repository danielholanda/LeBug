import logging as log
import sys, math, os, shutil, textwrap
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

        # Set parameters
        def setParameters(self,params):
            for p in params:
                parameter_name, parameter_value = p
                if parameter_name in self.module_class.parameter:
                    self.parameter[parameter_name]=parameter_value
                else:
                    assert False, f'{parameter_name} is not a parameter from {self.module_class.name}'

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

            # Ports map if the first name before the "_" is the same
            portMap={}
            for i in self.module_input:
                for j in signals_to_connect:
                    if i.bits==j.bits and i.name.split("_")[0]==j.name.split("_")[0]:
                        portMap[i.name]=j.name
            assert len(portMap.keys())==len(self.module_input), "Port map failed"
            self.instance_input=portMap

        def __init__(self,module_class,instance_name):
            self.module_class = module_class
            self.name = instance_name
            self.module_input=module_class.input
            self.module_output=module_class.output
            self.instance_input={}
            self.instance_output={}
            self.parameter={}

            # Map outputs using the name of the instance
            for o in module_class.output:
               self.instance_output[o.name]= struct(name=o.name+"_"+self.name,type=o.type,bits=o.bits) 

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

        def addParameter(self,params):
            for p in params:
                self.parameter.append(p)

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
            def apd(text):
                lines=text.split("\n")
                for l in lines:
                    rtlCode.append(ident+l)
            def apdi(text):
                lines=text.split("\n")
                for l in lines:
                    rtlCode.append(ident+"    "+l)
            
            # Add includes
            if self.includes!=[]:
                for i in self.includes:
                    apd('`include "'+i+'"')
                apd('')

            # Add declared module
            if self.input+self.output!=[]:
                apd('module  '+self.name+"(")
                # Add inputs and outputs
                for i in self.input:
                    bits= f'[{i.bits-1}:0]' if i.bits>1 else ''
                    comma = ',' if i!=self.input[-1] else ''
                    apd(f'  input {i.type} {bits} {i.name}{comma}')
                for i in self.output:
                    bits= f'[{i.bits-1}:0]' if i.bits>1 else ''
                    comma = ',' if i!=self.input[-1] else ''
                    apd(f'  output {i.type} {bits} {i.name}{comma}')
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
                    for key, value in inst.instance_output.items():
                        bits= f'[{value.bits-1}:0]' if value.bits>1 else ''
                        apdi(f'output {value.type} {bits} {value.name};')
                    # module name
                    apdi(inst.module_class.name+" "+inst.name+"(")
                    # Add parameters
                    if inst.parameter!={}:
                        apdi('#(')
                        apdi(',\n'.join([f'  parameter {key} = {value}' for key, value in inst.parameter.items()]))
                        apdi(')')
                    # Mapping inputs and outputs
                    inst_portmap=[]
                    apdi('(')
                    for key, value in inst.instance_input.items():
                        inst_portmap.append(f'  .{key}({value})')
                    for key, value in inst.instance_output.items():
                        inst_portmap.append(f'  .{key}({value.name})')
                    for i in inst_portmap:
                        if i!=inst_portmap[-1]:
                            apdi(i+",")
                        else:
                            apdi(i)
                    apdi(");")

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
            self.parameter=[]           # Store all parameters
            self.included=False         # Is true if the module has been imported
            self.dm=struct()            # Those are the declare modules
            self.im=struct()            # Those are the instantiated modules

    def rtlLogic(self):
        # Create RTL using custom RTL class
        rtl = self.rtlModule(self,"debugger")
        rtl.addInput([['clk','logic',1],['valid','logic',1],['eof','logic',1],['vector','logic',self.N]])

        # Adds includes to the beginning of the file
        rtl.include("inputBuffer.sv")

        # Tells the class about the included modules
        rtl.includeModule("inputBuffer")
        rtl.dm.inputBuffer.addInput([['clk_in','logic',1],['valid_in','logic',1],['eof_in','logic',1],['vector_in','logic',self.N]])
        rtl.dm.inputBuffer.addOutput([['valid_out','logic',1],['eof_out','logic',1],['vector_out','logic',self.N]])
        rtl.dm.inputBuffer.addParameter(['N','DATA_WIDTH','IB_DEPTH'])

        # Instantiate module
        rtl.instantiateModule(rtl.dm.inputBuffer,"ib")
        rtl.im.ib.connectInputs(rtl.input)
        rtl.im.ib.setParameters([['N',self.N],['DATA_WIDTH',self.DATA_WIDTH],['IB_DEPTH',self.IB_DEPTH]])

        # Declaring a Module
        #rtl.declareModule("testbench")
        #rtl.dm.testbench.addInput([['clk','logic',1],['vector','logic',self.N]])

        rtl.declareModule("Module2")

        # Prepare testbench
        testbench=[textwrap.dedent(f"""
        `timescale 1 ns/10 ps  // time-unit = 1 ns, precision = 10 ps
        module testbench;
            reg clk,valid,eof;
            reg vector [{self.N-1}:0];

            // duration for each bit = 20 * timescale = 20 * 1 ns  = 20ns
            localparam period = 20;  

            {rtl.name} dbg (.clk(clk), .vector(vector), .valid(valid), .eof(eof));
            
            initial
                begin
                    a = 0;
                    b = 0;
                    #period;
                end
        end
        """)]
        return rtl.dump()+testbench

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

    def __init__(self,N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH):
        ''' Verifying parameters '''
        assert math.log(N, 2).is_integer(), "N must be a power of 2" 
        assert math.log(M, 2).is_integer(), "N must be a power of 2" 
        assert M<=N, "M must be less or equal to N" 

        self.N=N
        self.M=M
        self.IB_DEPTH=IB_DEPTH
        self.DATA_WIDTH=DATA_WIDTH
        self.hwFolder = os.path.dirname(os.path.realpath(__file__))
        self.generateRtl()
        