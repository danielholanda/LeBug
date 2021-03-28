import sys
sys.path.insert(1, '../../src/')
from emulator.emulator import emulatedHw
from hardware.hardware import rtlHw
from misc.misc import *
import firmware.firmware as firm
import math
import numpy as np
np.set_printoptions(precision=3, suppress=False)

# Filter results after computations
def filterResults(emu_results, hw_results, DATA_TYPE):
    emu_results_filtered = emu_results['tb'][-1];
    if DATA_TYPE=='int':
        hw_results_filtered = np.array(toInt(hw_results['tb']['mem_data']))
    elif DATA_TYPE=='fixed_point':
        hw_results_filtered = np.array(encodedIntTofloat(hw_results['tb']['mem_data'],DATA_WIDTH))

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_results_filtered)
    print("\n********** Hardware results **********")
    print(hw_results_filtered)

    return emu_results_filtered, hw_results_filtered

# Read YAML configuration file and declare those as global variables
def readConf():
    with open(r'config.yaml') as file:
        yaml_dict = yaml.load(file, Loader=yaml.FullLoader)
        globals().update(yaml_dict)

# Put input values into testbench
def pushVals(emu_proc,hw_proc,num_input_vectors,eof1=None,eof2=None,neg_vals=False):
    np.random.seed(0)
    input_vectors=[]
    if eof1 is None:
        eof1=num_input_vectors*[False]
    if eof2 is None:
        eof2=num_input_vectors*[False]
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        # Integer data type
        if hw_proc.DATA_TYPE==0:
            input_vectors.append(np.random.randint(9, size=N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],eof1[i],eof2[i]])
        # Fixed-point data type
        elif hw_proc.DATA_TYPE==1:
            if neg_vals:
                input_vectors.append(10*np.random.random(N)-5)
            else:
                input_vectors.append(10*np.random.random(N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],eof1[i],eof2[i]])
            input_vectors[i] = floatToEncodedInt(input_vectors[i],hw_proc.DATA_WIDTH)
        hw_proc.push([input_vectors[i],eof1[i],eof2[i]])

def raw():

    # Instantiate HW and Emulator Processors
    readConf()
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,BUILDING_BLOCKS,DATA_TYPE,DEVICE_FAM)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    num_input_vectors=3
    pushVals(emu_proc,hw_proc,num_input_vectors,neg_vals=True)

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.raw(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=30
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_results_filtered, hw_results_filtered = filterResults(emu_results, hw_results, DATA_TYPE)

    # Verify that results are equal
    assert np.allclose(emu_results_filtered,hw_results_filtered,rtol=0.01)
    print("Passed test #1")

raw()

def multipleChains():

    # Instantiate HW and Emulator Processors
    readConf()
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,BUILDING_BLOCKS,DATA_TYPE,DEVICE_FAM)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    num_input_vectors=1
    pushVals(emu_proc,hw_proc,num_input_vectors,neg_vals=True)

    # Initialize the memories the same way
    emu_proc.initialize_fu=list(range(FUVRF_SIZE*M))
    hw_proc.initialize_fu=list(range(FUVRF_SIZE*M))

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.multipleChains(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=30
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_results_filtered, hw_results_filtered = filterResults(emu_results, hw_results, DATA_TYPE)

    # Verify that results are equal
    assert np.allclose(emu_results_filtered,hw_results_filtered, rtol=0.01)
    print("Passed test #2")

multipleChains()

def correlation():

    # Instantiate HW and Emulator Processors
    readConf()
    TB_SIZE=10
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,BUILDING_BLOCKS,DATA_TYPE,DEVICE_FAM)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    num_input_vectors=5
    pushVals(emu_proc,hw_proc,num_input_vectors,neg_vals=True)

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.correlation(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=30
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_results_filtered, hw_results_filtered = filterResults(emu_results, hw_results, DATA_TYPE)

    # Verify that results are equal
    assert np.allclose(emu_results_filtered,hw_results_filtered, rtol=0.05)
    print("Passed test #3")

correlation()


def conditions():

    # Instantiate HW and Emulator Processors
    readConf()
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,BUILDING_BLOCKS,DATA_TYPE,DEVICE_FAM)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    num_input_vectors=5
    eof1=[False,False,True,False,True]
    pushVals(emu_proc,hw_proc,num_input_vectors,eof1)

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.conditions(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=45
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_results_filtered, hw_results_filtered = filterResults(emu_results, hw_results, DATA_TYPE)

    # Verify that results are equal
    assert np.allclose(emu_results_filtered,hw_results_filtered, rtol=0.05)
    print("Passed test #4")

conditions()


def distribution():

    # Instantiate HW and Emulator Processors
    readConf()
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,BUILDING_BLOCKS,DATA_TYPE,DEVICE_FAM)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    num_input_vectors=2
    eof1=num_input_vectors*[True]
    pushVals(emu_proc,hw_proc,num_input_vectors,eof1)

    # Initialize the memories the same way
    emu_proc.initialize_fu=list(range(FUVRF_SIZE*M))
    hw_proc.initialize_fu=list(range(FUVRF_SIZE*M))

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.distribution(hw_proc.compiler,16,4)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=45
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_results_filtered, hw_results_filtered = filterResults(emu_results, hw_results, DATA_TYPE)

    # Verify that results are equal
    assert np.allclose(emu_results_filtered,hw_results_filtered)
    print("Passed test #5")

distribution()


def minicache_test():

    # Instantiate HW and Emulator Processors
    readConf()
    DATA_TYPE='int'
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,BUILDING_BLOCKS,DATA_TYPE,DEVICE_FAM)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    num_input_vectors=3
    eof1=num_input_vectors*[True]
    pushVals(emu_proc,hw_proc,num_input_vectors,eof1)

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.minicache(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=45
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_results_filtered, hw_results_filtered = filterResults(emu_results, hw_results, DATA_TYPE)

    # Verify that results are equal
    assert np.allclose(emu_results_filtered,hw_results_filtered,rtol=0.05)
    print("Passed test #6")

minicache_test()


def predictiveness():

    # Instantiate HW and Emulator Processors
    readConf()
    DATA_TYPE='int'
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorScalarReduce','VectorVectorALU','DataPacker','TraceBuffer']
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,BUILDING_BLOCKS,DATA_TYPE,DEVICE_FAM)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS) 

    # Create common input values
    num_input_vectors=4
    eof1=[False,True,False,True]
    eof2=[False,False,False,True]
    pushVals(emu_proc,hw_proc,num_input_vectors,eof1,eof2)

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.activationPredictiveness(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=45
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_results_filtered, hw_results_filtered = filterResults(emu_results, hw_results, DATA_TYPE)

    # Verify that results are equal
    assert np.allclose(emu_results_filtered,hw_results_filtered,rtol=0.05)
    print("Passed test #7")

predictiveness()