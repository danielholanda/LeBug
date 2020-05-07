import logging as log
import sys, math, os, shutil, textwrap, subprocess
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

# Run a given command using subprocess
def run(cmd):
    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
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
            for i in self.output:
                for _,j in submodule_outputs.items():
                    if i.bits==j.bits and i.name.split("_")[0]==j.name.split("_")[0]:
                        self.output_assignment[i.name]=j.name
            assert len(self.output_assignment.keys())==len(self.output), "Output map failed"

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
                for m in self.dm.__dict__.keys():
                    mod=self.dm.__dict__[m]
                    if mod.included==False:
                        rtlCode=rtlCode+mod.dump()
                
                # Instantiated modules
                for i in self.im.__dict__.keys():
                    inst=self.im.__dict__[i]
                    
                    # Declare outputs
                    apdi('')
                    apdi('\n'.join(f'output {value.type} [{value.bits}-1:0] {value.name} [{value.elements}-1:0];'.replace("[1-1:0]","") for key, value in inst.instance_output.items()))

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
            self.parent = parent        # name of Module
            self.includes=[]            # Stores include files
            self.wires=[]               # Stores wires
            self.regs=[]                # Stores regs
            self.input=[]               # Store all inputs logic ports
            self.output=[]              # Store all outputs logic ports
            self.output_assignment={}   # Describes how outputs are connected to internal signals
            self.parameter=[]           # Store all parameters
            self.included=False         # Is true if the module has been imported
            self.dm=struct()            # Those are the declare modules
            self.im=struct()            # Those are the instantiated modules

    def rtlLogic(self):
        # Create RTL using custom RTL class
        rtl = self.rtlModule(self,"debugger")
        rtl.addInput([['clk','logic',1],['valid_in','logic',1],['eof_in','logic',1],['vector_in','logic','DATA_WIDTH','N']])
        rtl.addOutput([['valid_out','logic',1],['vector_out','logic','DATA_WIDTH','N']])
        rtl.addParameter([['N',8],['DATA_WIDTH',32],['IB_DEPTH',4]])

        # Adds includes to the beginning of the file
        rtl.include("inputBuffer.sv")

        # Tells the class about the included modules
        rtl.includeModule("inputBuffer")
        rtl.dm.inputBuffer.addInput([['clk_in','logic',1],['valid_in','logic',1],['eof_in','logic',1],['vector_in','logic','DATA_WIDTH','N']])
        rtl.dm.inputBuffer.addOutput([['valid_out','logic',1],['eof_out','logic',1],['vector_out','logic','DATA_WIDTH','N']])
        rtl.dm.inputBuffer.addParameter([['N',8],['DATA_WIDTH',32],['IB_DEPTH',4]])

        # Instantiate modules
        rtl.instantiateModule(rtl.dm.inputBuffer,"ib")
        rtl.im.ib.setParameters([['N','N'],['DATA_WIDTH','DATA_WIDTH'],['IB_DEPTH','IB_DEPTH']])

        # Connect modules
        rtl.im.ib.connectInputs(rtl.input)
        rtl.assignOutputs(rtl.im.ib.instance_output)

        # Declaring a Module
        #rtl.declareModule("testbench")
        #rtl.dm.testbench.addInput([['clk','logic',1],['vector','logic',self.N]])

        # Prepare testbench inputs
        tb_inputs=[]
        for i in self.testbench_inputs:
            tb_inputs.append("valid = 1;")
            tb_inputs.append(f"eof = {int(i[1])};")
            for idx,ele in enumerate(i[0]):
                tb_inputs.append(f"vector[{idx}]=32'd{ele};")
            tb_inputs.append("toFile();")
            tb_inputs.append("#half_period;")
            tb_inputs.append("toFile();")
            tb_inputs.append("#half_period;")
            tb_inputs.append("")
        tb_inputs="\n\t\t\t\t\t\t\t\t\t\t".join(tb_inputs)

        # Prepare testbench steps
        tb_steps=[]
        for i in range(self.steps):
            tb_steps.append("valid = 0;")
            tb_steps.append("toFile();")
            tb_steps.append("#half_period;")
            tb_steps.append("toFile();")
            tb_steps.append("#half_period;")
            tb_steps.append("")
        tb_steps="\n\t\t\t\t\t\t\t\t\t\t".join(tb_steps)

        testbench=[textwrap.dedent(f"""
        `timescale 1 ns/10 ps  // time-unit = 1 ns, precision = 10 ps
        module testbench;

            // Compile-time parameters
            parameter N={self.N};
            parameter DATA_WIDTH={self.DATA_WIDTH};
            parameter IB_DEPTH={self.IB_DEPTH};

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
            {rtl.name} #(
              .N(N),
              .DATA_WIDTH(DATA_WIDTH),
              .IB_DEPTH(IB_DEPTH)
            )
            dbg(
              .clk(clk),
              .vector_in(vector),
              .valid_in(valid),
              .eof_in(eof),
              .valid_out(valid_out),
              .vector_out(vector_out)
            );
            
            //Task to print all content to file
            task toFile;
                begin
                    $fwrite(write_data, "%b %b %b", clk, valid, eof);
                    for (i = 0; i < {self.N}; i = i +1) begin
                        $fwrite(write_data, " %0d", vector[i]);
                    end
                    $fwrite(write_data, " %b", valid_out);
                    for (i = 0; i < {self.N}; i = i +1) begin
                        $fwrite(write_data, " %0d", vector_out[i]);
                    end
                    $fdisplay(write_data,"");
                
                end
            endtask

            // Test
            integer write_data,i;
            initial
                begin
                    write_data = $fopen("simulation_results.txt");
                    
                    $display("Test Started");
                    {tb_inputs}

                    {tb_steps}

                    $fclose(write_data);
                    $finish;
                end
        endmodule
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

    # This will run the testbench of the generated hardware and return its results
    def run(self,steps=50):
        # First, generate the RTL
        self.steps=steps
        self.generateRtl()

        # Then, run simulation
        current_folder=os.getcwd()
        rtl_folder=current_folder+"/rtl/"
        os.chdir(rtl_folder)
        run(['iverilog','-g2012', '-stestbench','-odebugProcessor','debugProcessor.sv'])
        run(['vvp','debugProcessor'])
        os.chdir(current_folder)

    def push(self,pushed_values):
        self.testbench_inputs.append(pushed_values)

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
        self.testbench_inputs=[]    # Stores inputs to testbench
        self.steps=0 # Number of steps for testbench
        