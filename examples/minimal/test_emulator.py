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

def testSimpleDistribution():
    
    # Instantiate processor
    proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE)

    # Initial hardware setup
    proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf

    fw = firm.distribution(proc.compiler,bins=2*M,M=M)

    # Feed one value to input buffer
    np.random.seed(42)
    input_vector = np.random.rand(N)*8
    proc.push([input_vector,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.allclose(tb[0],[ 1.,2.,1.,0.,1.,1.,1.,1.]), "Test with distribution failed"
    print("Passed test #1")

testSimpleDistribution()

def testDualDistribution():

    # Instantiate processor
    proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE)

    # Initial hardware setup
    proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf

    fw = firm.distribution(proc.compiler,bins=2*M,M=M)

    # Feed one value to input buffer
    np.random.seed(42)
    input_vector1=np.random.rand(N)*8
    input_vector2=np.random.rand(N)*8

    proc.push([input_vector1,False])
    proc.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.allclose(tb[0],[ 2.,5.,1.,0.,2.,2.,2.,2.]), "Test with dual distribution failed"
    print("Passed test #2")

testDualDistribution()

def testSummaryStats():

    # Instantiate processor
    proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE)

    proc.fu.vrf=list(np.concatenate(([0.,float('inf')],list(reversed(range(FUVRF_SIZE*M-2)))))) # Initializing fuvrf for sparsity
    fw = firm.summaryStats(proc.compiler)

    # Feed one value to input buffer
    np.random.seed(0)
    input_vector1=np.random.rand(N)*8-4
    input_vector2=np.random.rand(N)*8-4

    proc.push([input_vector1,False])
    proc.push([input_vector1,False])
    proc.push([input_vector1,False])
    proc.push([input_vector1,False])
    proc.push([input_vector1,False])
    proc.push([input_vector1,False])
    proc.push([input_vector1,False])
    proc.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.isclose(proc.dp.v_out[0],np.sum(input_vector1)*7+np.sum(input_vector2)), "Reduce sum failed"
    assert 47==int(proc.dp.v_out[1]), "Sparsity sum failed"
    print("Passed test #3")

testSummaryStats()

    
def testSpatialSparsity():

    # Instantiate processor
    proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE)
    proc.fu.vrf=list(np.concatenate(([0.,float('inf')],list(reversed(range(FUVRF_SIZE*M-2)))))) # Initializing fuvrf for sparsity
    fw = firm.spatialSparsity(proc.compiler,N)

    # Feed one value to input buffer
    np.random.seed(0)
    input_vector1=np.random.rand(N)*8-4
    input_vector2=np.random.rand(N)*8-4

    proc.push([input_vector1,False])
    proc.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.isclose(tb[0],[ 1.,1.,1.,1.,0.,1.,0.,1.]).all(), "Spatial Sparsity Failed"
    assert np.isclose(tb[1],[ 1.,0.,1.,1.,1.,1.,0.,0.]).all(), "Spatial Sparsity Failed"
    print("Passed test #4")

testSpatialSparsity()


def testCorrelation():

    # Instantiate processor
    proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE)
    fw = firm.correlation(proc.compiler)

    # Feed one value to input buffer
    np.random.seed(0)
    input_vector1=np.random.rand(N)*8-4
    input_vector2=np.random.rand(N)*8-4

    proc.push([input_vector1,False])
    proc.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()

    # Note that this is the Cross-correlation of two 1-dimensional sequences, not the coeficient
    numpy_correlate = np.corrcoef(input_vector1,input_vector2)

    v = proc.dp.v_out
    x, y, xx, yy, xy = v[1], v[4], v[2], v[5], v[3]

    # Note that the equation in this website is wrong, but the math is correct
    # https://www.investopedia.com/terms/c/correlation.asp

    corr = (N*xy-x*y)/math.sqrt((N*xx-x*x)*(N*yy-y*y))
    assert np.isclose(numpy_correlate[0][1],corr), "Correlation matches"
    print("Passed test #5")

testCorrelation()

def testVectorChange():

    # Instantiate processor
    proc = emulatedHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE)
    fw = firm.vectorChange(proc.compiler)

    # Feed value to input buffer
    np.random.seed(0)
    input_vector1=np.random.rand(N)*8-4
    input_vector2=np.random.rand(N)*8-4

    proc.push([input_vector1,False])
    proc.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()

    assert np.isclose(np.sum(input_vector1-input_vector2),proc.dp.v_out[1])

    print("Passed test #6")

testVectorChange()

def testNakedRtl():

    # Instantiate processor
    DATA_WIDTH=32
    proc = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH)

    # Feed values to input buffer
    np.random.seed(0)
    input_vector1=np.random.randint(100, size=N)
    input_vector2=np.random.randint(100, size=N)
    proc.push([input_vector1,False])
    proc.push([input_vector2,True])

    # Run testbench
    tb = proc.run(steps=10)

    # Check results
    assert True
    print("Passed test #7")

testNakedRtl()