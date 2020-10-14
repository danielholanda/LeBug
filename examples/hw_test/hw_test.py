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
    emu_proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE)

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
    steps=6
    hw_results = hw_proc.run(steps=steps,gui=False,log=False)
    emu_results = emu_proc.run(steps=steps)

    # Filter only the results we are interested in
    # Convert HW results to int (might contain "x"s and others)
    hw_ib_results=np.array(toInt(hw_results['ib']['vector_out']))
    emu_ib_results=np.array([v_out for v_out, eof_out, bof_out, chainId_out in emu_results['ib']])

    # Check results
    assert np.allclose(hw_ib_results,emu_ib_results), "Failed to match emulator and hardware in IB test"
    print("Passed test #1")

    print("Continue with UART support")



testNakedRtl()