import sys
sys.path.insert(1, '../../src/')
from emulator.emulator import emulatedHw
from hardware.hardware import rtlHw
import firmware.firmware as firm
import math, yaml
import numpy as np

# Read YAML configuration file and declare those as global variables
def readConf():
    with open(r'config.yaml') as file:
        yaml_dict = yaml.load(file, Loader=yaml.FullLoader)
        globals().update(yaml_dict)
readConf()

def toInt(lst):
    return [list(map(int, l)) for l in lst]

def testNakedRtl():

    # Missing: Select how components are attached to eachother

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vector1=np.random.randint(100, size=N)
    input_vector2=np.random.randint(100, size=N)

    # Push values to both procs
    hw_proc.push([input_vector1,False])
    hw_proc.push([input_vector2,True])
    emu_proc.push([input_vector1,False])
    emu_proc.push([input_vector2,True])

    # Configure firmware (missing HW firmware)
    fw = firm.passThrough(emu_proc.compiler)
    emu_proc.config(fw)

    # Run HW simulation and emulation
    steps=3
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter only the results we are interested in
    # Convert HW results to int (might contain "x"s and others)
    hw_ib_results=np.array(toInt(hw_results['ib']['vector_out']))
    emu_ib_results=np.array([v_out for v_out, eof_out, bof_out, chainId_out in emu_results['ib']])

    # Check results
    print("Expected:")
    print(emu_ib_results)
    print("\nHardware results:")
    print(hw_ib_results)
    assert np.allclose(hw_ib_results,emu_ib_results), "Failed to match emulator and hardware in IB test"
    print("Passed test #1")


#testNakedRtl()

def testVSRU():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'VectorScalarReduce']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vector1=np.random.randint(100, size=N)
    input_vector2=np.random.randint(100, size=N)

    # Push values to both procs
    hw_proc.push([input_vector1,False])
    hw_proc.push([input_vector2,True])
    emu_proc.push([input_vector1,False])
    emu_proc.push([input_vector2,True])

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.sumAll(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=8
    hw_results = hw_proc.run(steps=steps,gui=False,log=True)
    emu_results = emu_proc.run(steps=steps)

    # Filter only the results we are interested in
    # Convert HW results to int (might contain "x"s and others)
    hw_vsru_results=np.array(toInt(hw_results['vsru']['vector_out']))
    emu_vsru_results=np.array([v_out for v_out, eof_out, bof_out, chainId_out in emu_results['vsru']])

    # Check results
    print("\n\nExpected:")
    print(emu_vsru_results)
    print("\nHardware results:")
    print(hw_vsru_results)


    assert np.allclose(hw_vsru_results,emu_vsru_results), "Failed to match emulator and hardware in VSRU test"
    print("Passed test #2")

#testVSRU()

def testTB():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'VectorScalarReduce','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vector1=np.random.randint(100, size=N)
    input_vector2=np.random.randint(100, size=N)

    # Push values to both procs
    hw_proc.push([input_vector1,False])
    hw_proc.push([input_vector2,True])
    emu_proc.push([input_vector1,False])
    emu_proc.push([input_vector2,True])

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.raw(hw_proc.compiler)
    #emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=20
    hw_results = hw_proc.run(steps=steps,gui=False,log=True)
    #emu_results = emu_proc.run(steps=steps)

    # Filter only the results we are interested in
    # Convert HW results to int (might contain "x"s and others)
    hw_tb_results=np.array(hw_results['tb']['mem_data'])
    #emu_tb_results=emu_results['tb'][-1]

    # Check results
    #print("\n\nExpected:")
    #print(emu_vsru_results)
    print("\nHardware results:")
    print(hw_tb_results)

    #assert np.allclose(hw_vsru_results,emu_vsru_results), "Failed to match emulator and hardware in TB test"
    print("Passed test #3")

#testTB()


def testDataPacker():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=5
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=20
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        input_vectors.append(np.random.randint(100, size=N))
        hw_proc.push([input_vectors[i],False])
        emu_proc.push([input_vectors[i],False])
        print(f'Cycle {i}:\t{input_vectors[i]}')

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.sumAll(hw_proc.compiler)
    #fw = firm.raw(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=30
    hw_results = hw_proc.run(steps=steps,gui=False,log=True)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_trace_buffer = emu_results['tb'][-1];
    hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))

    # Print intermediate results
    #print("\n\n********** Intermediate Data Packer Results **********")
    #intermediate_results=np.array([print(f'{list(v_out)} valid:{valid}') for v_out, valid in emu_results['dp']])

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer), "Failed to match emulator and hardware in DP test"
    print("Passed test #4")

#testDataPacker()

def testVVALU():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=5
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=4
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        input_vectors.append(np.random.randint(5, size=N))
        hw_proc.push([input_vectors[i],False])
        emu_proc.push([input_vectors[i],False])
        print(f'Cycle {i}:\t{input_vectors[i]}')

    # Initialize the memories the same way
    emu_proc.vvalu.vrf = [1,2,3,4,5,6,7,8]*VVVRF_SIZE
    hw_proc.top.mod.vectorVectorALU.mem['vvrf']['init_values']=[[1,2,3,4,5,6,7,8]]*VVVRF_SIZE

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.vvalu_simple(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=35
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_trace_buffer = emu_results['tb'][-1];
    hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))

    # Print intermediate results
    #print("\n\n********** Intermediate Data Packer Results **********")
    #intermediate_results=np.array([print(f'{list(v_out)} valid:{valid}') for v_out, valid in emu_results['dp']])

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer), "Failed to match emulator and hardware in DP test"
    print("Passed test #4")

#testVVALU()

def testFRU():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=5
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=5
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        input_vectors.append(np.random.randint(5, size=N))
        hw_proc.push([input_vectors[i],False])
        emu_proc.push([input_vectors[i],False])
        print(f'Cycle {i}:\t{input_vectors[i]}')

    # Initialize the memories the same way
    emu_proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf
    hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[list(range(FUVRF_SIZE))]*M

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.fru_simple(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=30
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_trace_buffer = emu_results['tb'][-1];
    hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    #hw_trace_buffer = np.array(hw_results['tb']['mem_data'])

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer), "Failed to match emulator and hardware in FRU test"
    print("Passed test #5")

#testFRU()


def multipleChains():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=8
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=1
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        input_vectors.append(np.random.randint(5, size=N))
        hw_proc.push([input_vectors[i],False])
        emu_proc.push([input_vectors[i],False])
        print(f'Cycle {i}:\t{input_vectors[i]}')

    # Initialize the memories the same way
    emu_proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf
    hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[list(range(FUVRF_SIZE))]*M

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.multipleChains(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=30
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_trace_buffer = emu_results['tb'][-1];
    hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    #hw_trace_buffer = np.array(hw_results['tb']['mem_data'])

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer), "Failed to match emulator and hardware in FRU test"
    print("Passed test #6")

#multipleChains()


def correlation():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=10
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=3
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        input_vectors.append(np.random.randint(5, size=N))
        hw_proc.push([input_vectors[i],False])
        emu_proc.push([input_vectors[i],False])
        print(f'Cycle {i}:\t{input_vectors[i]}')

    # Initialize the memories the same way
    emu_proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf
    hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[list(range(FUVRF_SIZE))]*M

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.correlation(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=30
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_trace_buffer = emu_results['tb'][-1];
    hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    #hw_trace_buffer = np.array(hw_results['tb']['mem_data'])

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer), "Failed to match emulator and hardware in FRU test"
    print("Passed test #7")

#correlation()



def conditions():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=8
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=5
    np.random.seed(123)
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        eof = (i==3) or (i==5);
        input_vectors.append(np.random.randint(5, size=N))
        hw_proc.push([input_vectors[i],eof])
        emu_proc.push([input_vectors[i],eof])
        print(f'Cycle {i}:\t{input_vectors[i]}')

    # Initialize the memories the same way
    #emu_proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf
    #hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[list(range(FUVRF_SIZE))]*M
    emu_proc.vvalu.vrf = [1,1,1,1,1,1,1,1]*VVVRF_SIZE
    hw_proc.top.mod.vectorVectorALU.mem['vvrf']['init_values']=[[1,1,1,1,1,1,1,1]]*VVVRF_SIZE

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.conditions(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=45
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_trace_buffer = emu_results['tb'][-1];
    hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    #hw_trace_buffer = np.array(hw_results['tb']['mem_data'])

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer), "Failed to match emulator and hardware in FRU test"
    print("Passed test #8")

#conditions()


def distribution():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=8
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)


    def cnt(array,val):
        return len(np.where( array == val)[0])
    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=5
    np.random.seed(123)
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        eof = True;
        input_vectors.append(np.random.randint(9, size=N))
        hw_proc.push([input_vectors[i],eof])
        emu_proc.push([input_vectors[i],eof])
        print(f'Cycle {i}:\t{input_vectors[i]}')
        print(f'\t{cnt(input_vectors[i],0)} {cnt(input_vectors[i],1)} {cnt(input_vectors[i],2)} {cnt(input_vectors[i],3)} {cnt(input_vectors[i],4)} {cnt(input_vectors[i],5)} {cnt(input_vectors[i],6)} {cnt(input_vectors[i],7)}')

    # Initialize the memories the same way
    emu_proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf
    hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[list(a) for a in np.array_split(list(range(FUVRF_SIZE*M)), FUVRF_SIZE)]#[list(range(M))]*FUVRF_SIZE
    print(list(range(FUVRF_SIZE*M)))
    print([list(a) for a in np.array_split(list(range(FUVRF_SIZE*M)), FUVRF_SIZE)])
    #emu_proc.vvalu.vrf = [1,1,1,1,1,1,1,1]*VVVRF_SIZE
    #hw_proc.top.mod.vectorVectorALU.mem['vvrf']['init_values']=[[1,1,1,1,1,1,1,1]]*VVVRF_SIZE

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.distribution(hw_proc.compiler,8,4)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=45
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_trace_buffer = emu_results['tb'][-1];
    hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    #hw_trace_buffer = np.array(hw_results['tb']['mem_data'])

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer), "Failed to match emulator and hardware in FRU test"
    print("Passed test #8")

distribution()















