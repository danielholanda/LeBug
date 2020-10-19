import logging as log
import sys, math, os, shutil, textwrap, subprocess,shlex
from distutils.dir_util import copy_tree
from firmware.compiler import compiler
from misc.misc import *
import numpy as np
from containers.modelsim.modelsimContainer import modelsimContainer
import time

# Setting Debug level (can be debug, info, warning, error and critical)
log.basicConfig(stream=sys.stderr, level=log.INFO)

''' General settings '''
DEBUG=True

# Run a given command using subprocess
def run(cmd,wait=True):
    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if wait:
        proc.wait()

    # Print results
    result = proc.stdout.readlines()+proc.stderr.readlines()
    [ print(r.decode("utf-8"), end = '') for r in result]

class rtlHw():

    # This class describes an instantiated rtlModule
    class rtlInstance():

        # Set parameters
        def setParameters(self,params):
            for p in params:
                instance_parameter_name, instance_parameter_value = p
                module_parameter_names = [item[0] for item in self.module_class.parameter]
                if instance_parameter_name in module_parameter_names:
                    self.parameter[instance_parameter_name]=instance_parameter_value
                else:
                    assert False, f'{parameter_name} is not a parameter from {self.module_class.name}'

        # Connect inputs of instance
        def connectInputs(self,top_module_or_instance=None):
            
            # Check if we are connecting to the top module inputs or to an intance inside top
            if top_module_or_instance == None:
                signals_to_connect = []
            elif type(top_module_or_instance).__name__ == 'rtlInstance':
                signals_to_connect = [top_module_or_instance.instance_output[k] for k in top_module_or_instance.instance_output.keys()]
            elif type(top_module_or_instance).__name__ == 'rtlModule':
                signals_to_connect = top_module_or_instance.input[:]
            else:
                assert False

            # Add aditional signals that don't come from the module we are connecting to
            clock_signal_found=False
            config_signals_found=False
            for i in signals_to_connect:
                if i.name=='clk':
                    clock_signal_found=True
                if i.name=='config':
                    config_signals_found=True
            if not clock_signal_found:
                signals_to_connect.append(struct(name='clk',type='logic',bits=1))
            if not config_signals_found and top_module_or_instance != None:
                signals_to_connect.append(struct(name='tracing_comm',type='logic',bits=1,elements=1))
                if self.module_class.configurable_parameters!=0:
                    signals_to_connect.append(struct(name='configData_comm',type='logic',bits=8,elements=1))
                    signals_to_connect.append(struct(name='configId_comm',type='logic',bits=8,elements=1))

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
            self.mem=module_class.mem

            # Map outputs using the name of the instance
            for o in module_class.output:
               self.instance_output[o.name]= struct(name=o.name+"_"+self.name,type=o.type,bits=o.bits,elements=o.elements) 

    # This class describes an RTL module
    class rtlModule():

        # All include files go here
        def include(self,file):
            self.includes.append(file)

        def addInput(self,inputs):
            for i in inputs:
                elements = 1 if len(i)==3 else i[3]
                self.input.append(struct(name=i[0],type=i[1],bits=i[2],elements=elements))

        def addOutput(self,outputs):
            for o in outputs:
                elements = 1 if len(o)==3 else o[3]
                self.output.append(struct(name=o[0],type=o[1],bits=o[2],elements=elements))

        # Assign module outputs to the outputs of a given submodule
        def assignOutputs(self,submodule_outputs):
            submodule_outputs=submodule_outputs.instance_output
            for i in self.output:
                for _,j in submodule_outputs.items():
                    if i.bits==j.bits and i.name.split("_")[0]==j.name.split("_")[0]:
                        self.output_assignment[i.name]=j.name
            assert len(self.output_assignment.keys())==len(self.output), "Output map failed"

        def addParameter(self,params):
            for p in params:
                self.parameter.append(p)

        def addMemory(self,name,depth,width):
            self.mem[name]={}
            self.mem[name]['depth']=depth
            self.mem[name]['width']=width

        def setAsConfigurable(self,configurable_parameters):
            self.addInput([['tracing','logic',1],['configId','logic',8],['configData','logic',8]])
            self.configurable_parameters=configurable_parameters

        # Recursively adds Modules to module
        def declareModule(self,mod_name):
            if self.included==False:
                self.mod.__dict__[mod_name]=self.parent.rtlModule(self,mod_name)
            else:
                print("Can't declare Modules on imported modules")

        # Lets us know about Modules that have been imported 
        def includeModule(self,mod_name):
            self.declareModule(mod_name)
            self.mod.__dict__[mod_name].included=True

        # Instantiate a given module
        def instantiateModule(self,module_class,instance_name):
            self.inst.__dict__[instance_name]=self.parent.rtlInstance(module_class,instance_name)

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

            def dumpMifFile(mem):
                for mem_name in mem.keys():
                    f = open(f"rtl/{mem_name}.mif", "w")
                    f.write(f"Depth = {mem[mem_name]['depth']};\n")
                    f.write(f"Width = {mem[mem_name]['width']};\n")
                    f.write("Address_radix = dec;\n")
                    f.write("Data_radix = dec;\n")
                    f.write("Content\n")
                    f.write("Begin\n")
                    f.write(f"[0..{mem[mem_name]['depth']-1}] : 0;\n")
                    f.write("End;")
                    f.close()

            # Add includes
            if self.includes!=[]:
                for i in self.includes:
                    apd('`include "'+i+'"')
                apd('')

            # Add declared module
            if self.input+self.output!=[]:
                # Module name
                apd('module  '+self.name)

                # Module parameters
                apd("#(")
                apd(',\n'.join([f'  parameter {parameter_name} = {parameter_value}' for parameter_name, parameter_value in self.parameter]))
                apd(")")

                # Module inputs and outputs
                apd("(")
                apd('\n'.join(f'  input {i.type} [{i.bits}-1:0] {i.name} [{i.elements}-1:0],'.replace("[1-1:0]","") for i in self.input))
                apd(',\n'.join(f'  output {i.type} [{i.bits}-1:0] {i.name} [{i.elements}-1:0]'.replace("[1-1:0]","") for i in self.output))
                apd(');')

                # Do recursive dumps for submodules declared in this module
                for m in self.mod.__dict__.keys():
                    mod=self.mod.__dict__[m]
                    if mod.included==False:
                        rtlCode=rtlCode+mod.dump()

                # Instantiated modules
                for i in self.inst.__dict__.keys():
                    inst=self.inst.__dict__[i]

                    # Add mif file 
                    dumpMifFile(inst.mem)
                    
                    # Declare outputs
                    apdi('')
                    apdi('\n'.join(f'{value.type} [{value.bits}-1:0] {value.name} [{value.elements}-1:0];'.replace("[1-1:0]","") for key, value in inst.instance_output.items()))

                    # Print module class name
                    apdi(inst.module_class.name)

                    # Print parameters
                    if inst.parameter!={}:
                        apdi('#(')
                        apdi(',\n'.join([f'  .{key}({value})' for key, value in inst.parameter.items()]))
                        apdi(')')

                    # Print instance name, inputs and outputs
                    apdi(f'{inst.name}(')
                    apdi('\n'.join([f'  .{key}({value}),' for key, value in inst.instance_input.items()]))
                    apdi(',\n'.join([f'  .{key}({value.name})' for key, value in inst.instance_output.items()]))
                    apdi(");")

                # Create assertions for outputs
                apdi('')
                apdi('\n'.join([f'assign {key}={value};' for key, value in self.output_assignment.items()]))


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
            self.parent = parent            # parent Module
            self.includes=[]                # Stores include files
            self.wires=[]                   # Stores wires
            self.regs=[]                    # Stores regs
            self.input=[]                   # Store all inputs logic ports
            self.output=[]                  # Store all outputs logic ports
            self.output_assignment={}       # Describes how outputs are connected to internal signals
            self.parameter=[]               # Store all parameters
            self.included=False             # Is true if the module has been imported
            self.mod=struct()               # Those are the declare modules
            self.inst=struct()              # Those are the instantiated modules
            self.mem={}                     # Array of mems that need the mif files initialized
            self.configurable_parameters=0  # Number of configurable parameters of this module

    def rtlLogic(self):
        # Create TOP level module using custom RTL class
        top = self.rtlModule(self,"debugger")
        top.addInput([
            ['clk','logic',1],
            ['enqueue','logic',1],
            ['eof_in','logic',1],
            ['vector_in','logic','DATA_WIDTH','N']])
        top.addOutput([
            #['valid_out','logic',1],
            ['vector_out','logic','DATA_WIDTH','N']])
        top.addParameter([
            ['N',8],
            ['DATA_WIDTH',32],
            ['IB_DEPTH',4],
            ['MAX_CHAINS',4],
            ['TB_SIZE',64]])

        # Adds includes to the beginning of the file
        top.include("input_buffer.sv")
        top.include("trace_buffer.sv")
        top.include("vector_scalar_reduce_unit.sv")
        top.include("uart.sv")

        # UART module
        top.includeModule("uart")
        top.mod.uart.addInput([['clk','logic',1]])
        top.mod.uart.addOutput([
            ['tracing','logic',1],
            ['configId','logic',8],
            ['configData','logic',8]])

        # Input buffer
        top.includeModule("inputBuffer")
        top.mod.inputBuffer.addInput([
            ['clk','logic',1],
            ['enqueue','logic',1],
            ['eof_in','logic',1],
            ['vector_in','logic','DATA_WIDTH','N']])
        top.mod.inputBuffer.addOutput([
            ['valid_out','logic',1],
            ['eof_out','logic',1],
            ['vector_out','logic','DATA_WIDTH','N'],
            ['chainId_out','logic',1]])
        top.mod.inputBuffer.addParameter([
            ['N',8],['DATA_WIDTH',32],['IB_DEPTH',4]])
        top.mod.inputBuffer.addMemory("inputBuffer",self.IB_DEPTH,self.DATA_WIDTH*self.N)
        top.mod.inputBuffer.setAsConfigurable(configurable_parameters=4)

        # Vector Scalar Reduce unit
        top.includeModule("vectorScalarReduceUnit")
        top.mod.vectorScalarReduceUnit.addInput([
            ['clk','logic',1],
            ['valid_in','logic',1],
            ['eof_in','logic',1],
            ['chainId_in','logic',1],
            ['vector_in','logic','DATA_WIDTH','N']])
        top.mod.vectorScalarReduceUnit.addOutput([
            ['valid_out','logic',1],
            ['vector_out','logic','DATA_WIDTH','N']])
        top.mod.vectorScalarReduceUnit.addParameter([
            ['N',8],
            ['DATA_WIDTH',32],
            ['MAX_CHAINS',4],
            ['PERSONAL_CONFIG_ID',0],
            ['INITIAL_FIRMWARE',"'{MAX_CHAINS{0}}"]])
        top.mod.vectorScalarReduceUnit.setAsConfigurable(configurable_parameters=4)

        # TraceBuffer
        top.includeModule("traceBuffer")
        top.mod.traceBuffer.addInput([
            ['clk','logic',1],
            ['valid_in','logic',1],
            ['vector_in','logic','DATA_WIDTH','N'],
            ['tracing','logic',1]])
        top.mod.traceBuffer.addOutput([
            ['vector_out','logic','DATA_WIDTH','N']])
        top.mod.traceBuffer.addParameter([
            ['N',8],
            ['DATA_WIDTH',32],
            ['TB_SIZE',64]])
        top.mod.traceBuffer.addMemory("traceBuffer",self.TB_SIZE,self.DATA_WIDTH*self.N)

        # Convert FW to RTL
        if self.firmware is None:
            VSRU_INITIAL_FIRMWARE = "'{MAX_CHAINS{0}}"
        else:
            VSRU_INITIAL_FIRMWARE=str([chain.op for chain in self.firmware['vsru']]).replace("[", "'{").replace("]", "}")

        # Instantiate modules
        top.instantiateModule(top.mod.uart,"comm")

        top.instantiateModule(top.mod.inputBuffer,"ib")
        top.inst.ib.setParameters([
            ['N','N'],
            ['DATA_WIDTH','DATA_WIDTH'],
            ['IB_DEPTH','IB_DEPTH']])

        top.instantiateModule(top.mod.vectorScalarReduceUnit,"vsru")
        top.inst.vsru.setParameters([
            ['N','N'],
            ['DATA_WIDTH','DATA_WIDTH'],
            ['MAX_CHAINS','MAX_CHAINS'],
            ['PERSONAL_CONFIG_ID','0'],
            ['INITIAL_FIRMWARE',VSRU_INITIAL_FIRMWARE]])

        top.instantiateModule(top.mod.traceBuffer,"tb")
        top.inst.tb.setParameters([
            ['N','N'],
            ['DATA_WIDTH','DATA_WIDTH'],
            ['TB_SIZE','TB_SIZE']])

        # Connect modules
        top.inst.comm.connectInputs() 
        top.inst.ib.connectInputs(top) 
        top.inst.vsru.connectInputs(top.inst.ib)
        top.inst.tb.connectInputs(top.inst.vsru)
        top.assignOutputs(top.inst.tb)
        self.top=top
        return top.dump()

    def testbench(self):
        # Prepare testbench inputs
        tb_inputs=[]
        for i in self.testbench_inputs:
            tb_inputs.append("valid = 1;")
            tb_inputs.append(f"eof = {int(i[1])};")
            for idx,ele in enumerate(i[0]):
                tb_inputs.append(f"vector[{idx}]=32'd{ele};")
            tb_inputs.append("#half_period;")
            tb_inputs.append("#half_period;")
            tb_inputs.append("")
        tb_inputs=("\n"+"    "*4).join(tb_inputs)

        # Prepare testbench steps
        tb_steps=[]
        for i in range(self.steps):
            tb_steps.append("valid = 0;")
            tb_steps.append("toFile();")
            tb_steps.append("#half_period;")
            tb_steps.append("#half_period;")
            tb_steps.append("")
        tb_steps=("\n"+"    "*4).join(tb_steps)

        # Prepare testbench values to save to file
        tb_store=[]
        tb_var_names={}
        for i in self.top.inst.__dict__.keys():
            inst=self.top.inst.__dict__[i]
            tb_var_names[inst.name]=[]
            for o in inst.module_output:
                tb_var_names[inst.name].append([o.name,o.elements])
                if o.elements==1:
                    tb_store.append(f'$fwrite(write_data, "%{"b" if o.bits==1 else "0d"} ",dbg.{inst.name}.{o.name});')
                else:
                    if not o.elements.isnumeric():
                        tb_store.append(f"for (i=0; i<dbg.{inst.name}.{o.elements}; i=i+1) begin")
                    else:
                        tb_store.append(f"for (i=0; i<{o.elements}; i=i+1) begin")
                    tb_store.append(f'\t$fwrite(write_data, "%{"b" if o.bits==1 else "0d"} ",dbg.{inst.name}.{o.name}[i]);')
                    tb_store.append("end")
        tb_store.append('$fdisplay(write_data,"");')
        tb_store=("\n"+"    "*4).join(tb_store)

        # Add includes
        testbench='`include "debugProcessor.sv"\n'

        testbench=[testbench+textwrap.dedent(f"""
        `timescale 1 ns/10 ps  // time-unit = 1 ns, precision = 10 ps
        module testbench;

            // Compile-time parameters
            parameter N={self.N};
            parameter DATA_WIDTH={self.DATA_WIDTH};
            parameter IB_DEPTH={self.IB_DEPTH};
            parameter MAX_CHAINS={self.MAX_CHAINS};
   
            // Declare inputs
            reg clk=1'b0;
            reg valid,eof;
            reg [DATA_WIDTH-1:0] vector [N-1:0];
            
            // Declare outputs
            reg [DATA_WIDTH-1:0] vector_out [N-1:0];
            reg valid_out;
            
            // duration for each bit = 10 * timescale = 10 * 1 ns  = 10ns
            localparam period = 10; 
            localparam half_period = 5; 
            
            always #half_period clk=~clk; 
            
            // Instantiate debugger
            {self.top.name} #(
              .N(N),
              .DATA_WIDTH(DATA_WIDTH),
              .IB_DEPTH(IB_DEPTH),
              .MAX_CHAINS(MAX_CHAINS)
            )
            dbg(
              .clk(clk),
              .vector_in(vector),
              .enqueue(valid),
              .eof_in(eof),
              .vector_out(vector_out)
            );

            //Task to print all content to file
            integer write_data,i,j;
            task toFile;
                begin
                {tb_store}
                end
            endtask

            // Test
            initial begin
                write_data = $fopen("simulation_results.txt");
                
                $display("Test Started");
                {tb_inputs}
                
                {tb_steps}
                
                $fclose(write_data);
                $finish;
            end
        endmodule
        """)]

        self.tb_var_names=tb_var_names
        return testbench

    def generateRtl(self):

        # Create subfolder where all files will be generated
        rtl_folder=os.getcwd()+"/rtl"
        if os.path.isdir(rtl_folder):
            shutil.rmtree(rtl_folder)
        os.mkdir(rtl_folder)
        copy_tree(self.hwFolder+"/buildingBlocks", rtl_folder)
        copy_tree(self.hwFolder+"/simulationBlocks", rtl_folder)

        # Writes debugProcessor to file
        f = open(rtl_folder+"/debugProcessor.sv", "w")
        for l in self.rtlLogic():
            f.write(l+"\n")
        f.close()

        # Writes testbench to file
        f = open(rtl_folder+"/testbench.sv", "w")
        for l in self.testbench():
            f.write(l+"\n")
        f.close()

    def config(self,fw):
        #Configure processor
        self.firmware=fw

    # This will run the testbench of the generated hardware and return its results
    def run(self,steps=50,gui=False,log=True):
        # First, generate the RTL
        self.steps=steps
        self.generateRtl()

        # Then, run simulation
        current_folder=os.getcwd()
        rtl_folder=current_folder+"/rtl/"
        os.chdir(rtl_folder)

        modelsim = modelsimContainer(log)
        modelsim.start()
        modelsim.exec('mkdir rtl')
        modelsim.copy(rtl_folder,'modelsim:.')
        modelsim.exec('vlib work',working_directory='/rtl')
        modelsim.exec('vlog altera_mf.v testbench.sv',working_directory='/rtl')
        if gui:
            print("Opening GUI\n\tMake sure to open socket using this command on your mac:\n\tsocat TCP-LISTEN:6000,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\"")
            modelsim.exec('vsim -gui -do "run -all" testbench',working_directory='/rtl')
        else:
            modelsim.exec('vsim -c -do "run -all" testbench',working_directory='/rtl')
        modelsim.copy('modelsim:/rtl/simulation_results.txt','simulation_results.txt')
        modelsim.exec('rm -r rtl')
        modelsim.stop()

        # Get results from file back to python
        results={}
        for mod in self.tb_var_names.keys():
                results[mod]={}
                for var_name, elements in self.tb_var_names[mod]:
                    results[mod][var_name]=[]
        f = open("simulation_results.txt", "r")
        for line in f:
            count=0
            l= line.replace("\n","").split(" ")
            for mod in self.tb_var_names.keys():
                for var_name, elements in self.tb_var_names[mod]:
                    if elements=='N':
                        elements=self.N
                    results[mod][var_name].append(l[count:count+elements])
                    count=count+elements

        # Go back to main directory
        os.chdir(current_folder)

        return results

    def push(self,pushed_values):
        self.testbench_inputs.append(pushed_values)

    def __init__(self,N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS):
        ''' Verifying parameters '''
        assert math.log(N, 2).is_integer(), "N must be a power of 2" 
        assert math.log(M, 2).is_integer(), "N must be a power of 2" 
        assert M<=N, "M must be less or equal to N" 

        self.N=N
        self.M=M
        self.IB_DEPTH=IB_DEPTH
        self.DATA_WIDTH=DATA_WIDTH
        self.MAX_CHAINS=MAX_CHAINS
        self.TB_SIZE=TB_SIZE
        self.hwFolder = os.path.dirname(os.path.realpath(__file__))
        self.testbench_inputs=[]    # Stores inputs to testbench
        self.steps=0 # Number of steps for testbench
        self.top=None # used to store all rtl info later on
        self.tb_var_names = None
        self.compiler = compiler(M,N,MAX_CHAINS)
        self.firmware = None
        