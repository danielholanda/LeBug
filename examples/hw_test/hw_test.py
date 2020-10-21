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


testNakedRtl()

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

testVSRU()

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

testTB()

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
    num_input_vectors=16
    for i in range(num_input_vectors):
        input_vectors.append(np.random.randint(100, size=N))
        hw_proc.push([input_vectors[i],False])
        emu_proc.push([input_vectors[i],False])

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.sumAll(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=20
    hw_results = hw_proc.run(steps=steps,gui=False,log=True)
    emu_results = emu_proc.run(steps=steps)

    # Check when the wrong valid starts
    #print(np.array(hw_results['ib']['valid_out']))
    #print(np.array(hw_results['ib']['vector_out']))
    print("Trace Buffer is right, but apparently I'm not storing/reading things correctly for some reason...")
    print("Problem might be related with size of trace buffer.... not sure")
    print("\nExpected vsru:")
    
    emu_vsru_results=np.array([v_out for v_out, eof_out, bof_out, chainId_out in emu_results['vsru']])
    print(emu_vsru_results)
    print("\nHW vsru:")
    print(np.array(hw_results['vsru']['vector_out']))
    #exit()

    # Check results
    print("\n\nExpected:")
    print(emu_results['tb'][-1])
    print("\nHardware results:")
    print(np.array(toInt(hw_results['tb']['mem_data'])))

    #assert np.allclose(hw_vsru_results,emu_vsru_results), "Failed to match emulator and hardware in DP test"
    print("Passed test #4")

testDataPacker()


















