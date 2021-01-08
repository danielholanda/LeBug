import sys
sys.path.insert(1, '../../src/')
from emulator.emulator import emulatedHw
from hardware.hardware import rtlHw
import firmware.firmware as firm
import math, yaml
import numpy as np
np.set_printoptions(precision=3, suppress=False)

# Read YAML configuration file and declare those as global variables
def readConf():
    with open(r'config.yaml') as file:
        yaml_dict = yaml.load(file, Loader=yaml.FullLoader)
        globals().update(yaml_dict)
readConf()

def toInt(lst):
    return [list(map(int, l)) for l in lst]

print("BUG1: STRATIX10 DUAL_PORT_RAM IS WORKING DIFFERENTLY FROM CYCLONE V DUAL_PORT_RAM")
print("BUG2: ENCODE/DECODE ONLY WORK FOR POSITIVE NUMBERS")

def floatToEncodedInt(float_array,DATA_WIDTH):
    return [encode(x,DATA_WIDTH) for x in float_array]
    
def encode(value,DATA_WIDTH):
    int_bits=int(DATA_WIDTH/2)
    frac_bits=int(DATA_WIDTH/2)
    max_value = (1<<(int_bits-1+frac_bits))-1
    min_value = -(1<<(int_bits-1+frac_bits))
    x =  round(value * (1<< frac_bits))
    return int(min_value if x<min_value else max_value if x > max_value else x)

def encodedIntTofloat(encoded_int,DATA_WIDTH):
    frac_bits=int(DATA_WIDTH/2)
    return [[float(encoded_value) / (1 << frac_bits) for encoded_value in l] for l in encoded_int]

def raw():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=8
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,DATA_TYPE,EXP_WIDTH)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=3
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        if DATA_TYPE=='int':
            input_vectors.append(np.random.randint(5, size=N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],False])
            hw_proc.push([input_vectors[i],False])
        elif DATA_TYPE=='fixed_point':
            input_vectors.append(5*np.random.random(N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],False])
            input_vectors[i] = floatToEncodedInt(input_vectors[i],DATA_WIDTH)
            hw_proc.push([input_vectors[i],False])

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.raw(hw_proc.compiler)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=30
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_trace_buffer = emu_results['tb'][-1];
    if DATA_TYPE=='int':
        hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    elif DATA_TYPE=='fixed_point':
        hw_trace_buffer = np.array(encodedIntTofloat(hw_results['tb']['mem_data'],DATA_WIDTH))
    #hw_trace_buffer = np.array(hw_results['tb']['mem_data'])

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer,rtol=0.01)
    print("Passed test #1")

raw()


def multipleChains():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=8
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,DATA_TYPE,EXP_WIDTH)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=1
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        if DATA_TYPE=='int':
            input_vectors.append(np.random.randint(5, size=N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],False])
            hw_proc.push([input_vectors[i],False])
        elif DATA_TYPE=='fixed_point':
            input_vectors.append(5*np.random.random(N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],False])
            input_vectors[i] = floatToEncodedInt(input_vectors[i],DATA_WIDTH)
            hw_proc.push([input_vectors[i],False])

    # Initialize the memories the same way
    emu_proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf
    if DATA_TYPE=='int':
        hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[list(range(FUVRF_SIZE))]*M
    elif DATA_TYPE=='fixed_point':
        hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[floatToEncodedInt(list(range(FUVRF_SIZE)),DATA_WIDTH)]*M

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
    if DATA_TYPE=='int':
        hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    elif DATA_TYPE=='fixed_point':
        hw_trace_buffer = np.array(encodedIntTofloat(hw_results['tb']['mem_data'],DATA_WIDTH))

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer, rtol=0.01)
    print("Passed test #2")

multipleChains()


def correlation():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=10
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,DATA_TYPE,EXP_WIDTH)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=3
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        if DATA_TYPE=='int':
            input_vectors.append(np.random.randint(5, size=N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],False])
            hw_proc.push([input_vectors[i],False])
        elif DATA_TYPE=='fixed_point':
            input_vectors.append(5*np.random.random(N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],False])
            input_vectors[i] = floatToEncodedInt(input_vectors[i],DATA_WIDTH)
            hw_proc.push([input_vectors[i],False])

    # Initialize the memories the same way
    emu_proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf
    if DATA_TYPE=='int':
        hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[list(range(FUVRF_SIZE))]*M
    elif DATA_TYPE=='fixed_point':
        hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[floatToEncodedInt(list(range(FUVRF_SIZE)),DATA_WIDTH)]*M

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
    if DATA_TYPE=='int':
        hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    elif DATA_TYPE=='fixed_point':
        hw_trace_buffer = np.array(encodedIntTofloat(hw_results['tb']['mem_data'],DATA_WIDTH))

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer, rtol=0.01)
    print("Passed test #3")

correlation()


def conditions():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=8
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,DATA_TYPE,EXP_WIDTH)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=5
    np.random.seed(123)
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        eof = (i==3) or (i==5);
        if DATA_TYPE=='int':
            input_vectors.append(np.random.randint(5, size=N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],eof])
            hw_proc.push([input_vectors[i],eof])
        elif DATA_TYPE=='fixed_point':
            input_vectors.append(5*np.random.random(N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],eof])
            input_vectors[i] = floatToEncodedInt(input_vectors[i],DATA_WIDTH)
            hw_proc.push([input_vectors[i],eof])

    # Initialize the memories the same way
    emu_proc.vvalu.vrf = [1,1,1,1,1,1,1,1]*VVVRF_SIZE
    if DATA_TYPE=='int':
        hw_proc.top.mod.vectorVectorALU.mem['vvrf']['init_values']=[[1,1,1,1,1,1,1,1]]*VVVRF_SIZE
    elif DATA_TYPE=='fixed_point':
        hw_proc.top.mod.vectorVectorALU.mem['vvrf']['init_values']=[floatToEncodedInt([1,1,1,1,1,1,1,1],DATA_WIDTH)]*VVVRF_SIZE

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
    if DATA_TYPE=='int':
        hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    elif DATA_TYPE=='fixed_point':
        hw_trace_buffer = np.array(encodedIntTofloat(hw_results['tb']['mem_data'],DATA_WIDTH))

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer)
    print("Passed test #4")

conditions()


def distribution():

    # Overwrite YAML file to define how components are attached to eachother
    BUILDING_BLOCKS=['InputBuffer', 'FilterReduceUnit','VectorVectorALU','VectorScalarReduce','DataPacker','TraceBuffer']

    # Instantiate HW and Emulator Processors
    DATA_WIDTH=32
    MAX_CHAINS=4
    IB_DEPTH=32
    TB_SIZE=8
    hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,DATA_TYPE,EXP_WIDTH)
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,MAX_CHAINS,BUILDING_BLOCKS)

    # Create common input values
    np.random.seed(0)
    input_vectors=[]
    num_input_vectors=5
    np.random.seed(123)
    print("********** Input vectors **********")
    for i in range(num_input_vectors):
        eof = True;
        if DATA_TYPE=='int':
            input_vectors.append(np.random.randint(9, size=N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],eof])
            hw_proc.push([input_vectors[i],eof])
        elif DATA_TYPE=='fixed_point':
            input_vectors.append(9*np.random.random(N))
            print(f'Cycle {i}:\t{input_vectors[i]}')
            emu_proc.push([input_vectors[i],eof])
            input_vectors[i] = floatToEncodedInt(input_vectors[i],DATA_WIDTH)
            hw_proc.push([input_vectors[i],eof])

    # Initialize the memories the same way
    emu_proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf
    if DATA_TYPE=='int':
        hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[list(a) for a in np.array_split(list(range(FUVRF_SIZE*M)), FUVRF_SIZE)]
    elif DATA_TYPE=='fixed_point':
        hw_proc.top.mod.filterReduceUnit.mem['furf']['init_values']=[floatToEncodedInt(a,DATA_WIDTH) for a in np.array_split(list(range(FUVRF_SIZE*M)), FUVRF_SIZE)]

    # Configure firmware - Both HW and Emulator work with the same firmware
    fw = firm.distribution(hw_proc.compiler,16,4)
    emu_proc.config(fw)
    hw_proc.config(fw)

    # Run HW simulation and emulation
    steps=45
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter Results
    emu_trace_buffer = emu_results['tb'][-1];
    if DATA_TYPE=='int':
        hw_trace_buffer = np.array(toInt(hw_results['tb']['mem_data']))
    elif DATA_TYPE=='fixed_point':
        hw_trace_buffer = np.array(encodedIntTofloat(hw_results['tb']['mem_data'],DATA_WIDTH))

    # Print Results
    print("\n\n********** Emulation results **********")
    print(emu_trace_buffer)
    print("\n********** Hardware results **********")
    print(hw_trace_buffer)

    # Verify that results are equal
    assert np.allclose(emu_trace_buffer,hw_trace_buffer)
    print("Passed test #5")

distribution()















