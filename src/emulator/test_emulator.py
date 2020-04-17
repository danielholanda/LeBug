from emulator import *
import math

def testSimpleDistribution():
    
    # Instantiate processor
    proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)

    # Initial hardware setup
    proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf

    # Firmware for a generic distribution
    def distribution(bins):
        assert bins%M==0, "Number of bins must be divisible by M for now"
        cp = compiler()
        for i in range(bins/M):
            cp.begin_chain()
            cp.vv_filter(i)
            cp.m_reduce(axis='M')
            cp.vv_add(i)
            cp.v_commit(M)
            cp.end_chain()
        return cp.compile()

    fw = distribution(2*M)

    # Feed one value to input buffer
    np.random.seed(42)
    input_vector = np.random.rand(N)*8
    proc.ib.push([input_vector,False])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.allclose(tb[0],[ 1.,2.,1.,0.,1.,1.,1.,1.]), "Test with distribution failed"
    print("Passed test #1")

testSimpleDistribution()

def testDualDistribution():

    # Instantiate processor
    proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)

    # Initial hardware setup
    proc.fu.vrf=list(range(FUVRF_SIZE*M)) # Initializing fuvrf

    # Firmware for a distribution with 2 sets of N values
    def distribution(bins):
        assert bins%M==0, "Number of bins must be divisible by M for now"
        cp = compiler()
        for i in range(bins/M):
            cp.begin_chain()
            cp.vv_filter(i)
            cp.m_reduce('M')
            cp.vv_add(i,'notfirst')
            cp.v_cache(i)
            cp.v_commit(M,'last')
            cp.end_chain()
        return cp.compile()

    fw = distribution(2*M)

    # Feed one value to input buffer
    np.random.seed(42)
    input_vector1=np.random.rand(N)*8
    input_vector2=np.random.rand(N)*8

    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.allclose(tb[0],[ 2.,5.,1.,0.,2.,2.,2.,2.]), "Test with dual distribution failed"
    print("Passed test #2")

testDualDistribution()

def testSummaryStats():

    # Instantiate processor
    proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)
    cp = compiler()

    proc.fu.vrf=list(np.concatenate(([0.,float('inf')],list(reversed(range(FUVRF_SIZE*M-2)))))) # Initializing fuvrf for sparsity


    # Firmware for a distribution with 2 sets of N values
    def summaryStats():
        
        # Sum of all values
        cp.begin_chain()
        cp.vv_add(0,'notfirst')
        cp.v_cache(0)
        cp.v_reduce()
        cp.v_commit(1,'last')
        cp.end_chain()

        # Number of sparse elements
        cp.begin_chain()
        cp.vv_filter(0)
        cp.m_reduce('N')
        cp.vv_add(1,'notfirst')
        cp.v_cache(1)
        cp.v_reduce()
        cp.v_commit(1,'last')
        cp.end_chain()
        return cp.compile()

    fw = summaryStats()

    # Feed one value to input buffer
    np.random.seed(0)
    input_vector1=np.random.rand(N)*8-4
    input_vector2=np.random.rand(N)*8-4

    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.isclose(proc.dp.v_out[0],np.sum(input_vector1)*7+np.sum(input_vector2)), "Reduce sum failed"
    assert 47==int(proc.dp.v_out[1]), "Sparsity sum failed"
    print("Passed test #3")

testSummaryStats()

    
def testSpatialSparsity():

    # Instantiate processor
    proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)
    cp = compiler()

    proc.fu.vrf=list(np.concatenate(([0.,float('inf')],list(reversed(range(FUVRF_SIZE*M-2)))))) # Initializing fuvrf for sparsity


    # Firmware for a distribution with 2 sets of N values
    def summaryStats():

        # Spatial sparsity
        cp.begin_chain()
        cp.vv_filter(0)
        cp.m_reduce('N')
        cp.v_commit(N)
        cp.end_chain()
        return cp.compile()

    fw = summaryStats()

    # Feed one value to input buffer
    np.random.seed(0)
    input_vector1=np.random.rand(N)*8-4
    input_vector2=np.random.rand(N)*8-4

    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()
    assert np.isclose(tb[0],[ 1.,1.,1.,1.,0.,1.,0.,1.]).all(), "Spatial Sparsity Failed"
    assert np.isclose(tb[1],[ 1.,0.,1.,1.,1.,1.,0.,0.]).all(), "Spatial Sparsity Failed"
    print("Passed test #4")

testSpatialSparsity()


def testCorrelation():

    # Instantiate processor
    proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)
    cp = compiler()

    # Firmware for a distribution with 2 sets of N values
    def correlation():

        # sum(X*Y) [Assuming that Y is stored in addr0]
        cp.begin_chain()
        cp.vv_mul(0)
        cp.v_reduce()
        cp.v_commit(1)
        cp.end_chain()

        # sum(X) [Storing X in addr0, which will become the Y of next vector]
        cp.begin_chain()
        cp.v_cache(0)
        cp.v_reduce()
        cp.v_commit(1)
        cp.end_chain()

        # sum(X*X)
        cp.begin_chain()
        cp.vv_mul(0)
        cp.v_reduce()
        cp.v_commit(1)
        cp.end_chain()
        return cp.compile()

    fw = correlation()

    # Feed one value to input buffer
    np.random.seed(0)
    input_vector1=np.random.rand(N)*8-4
    input_vector2=np.random.rand(N)*8-4

    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector2,True])

    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()

    # Note that this is the Cross-correlation of two 1-dimensional sequences, not the coeficient
    numpy_correlate = np.corrcoef(input_vector1,input_vector2)

    v = proc.dp.v_out
    x, y, xx, yy, xy = v[1], v[4], v[2], v[5], v[3]
    #x, y, xx, yy, xy = np.sum(input_vector1), np.sum(input_vector2), np.sum(input_vector1*input_vector1), np.sum(input_vector2*input_vector2), np.sum(input_vector1*input_vector2)

    # Note that the equation in this website is wrong, but the math is correct
    # https://www.investopedia.com/terms/c/correlation.asp

    corr = (N*xy-x*y)/math.sqrt((N*xx-x*x)*(N*yy-y*y))
    assert np.isclose(numpy_correlate[0][1],corr), "Correlation matches"
    print("Passed test #5")

testCorrelation()

def testVectorChange():

    # Instantiate processor
    proc = CISC(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE)
    cp = compiler()

    # Firmware for a distribution with 2 sets of N values
    def vectorChange():

        # Commit difference between current and previous sample
        cp.begin_chain()
        cp.vv_sub(0)
        cp.v_reduce()
        cp.v_commit(1)
        cp.end_chain()

        # Save vector to mem0
        cp.begin_chain()
        cp.v_cache(0)
        cp.end_chain()
        return cp.compile()

    fw = vectorChange()

    # Feed one value to input buffer
    np.random.seed(0)
    input_vector1=np.random.rand(N)*8-4
    input_vector2=np.random.rand(N)*8-4

    proc.ib.push([input_vector1,False])
    proc.ib.push([input_vector2,True])


    # Step through it until we get the result
    proc.config(fw)
    tb = proc.run()

    assert np.isclose(np.sum(input_vector1-input_vector2),proc.dp.v_out[1])

    print("Passed test #6")

testVectorChange()

# Ideas for new instruments:
# 1- Check elements that are between -inf and min_range OR NaN OR between max_range and Inf (given a specific activation)
#   In the previous instrumentation, I would need one instrument for each of them (3x more memory)
# 2- How often is the entire vector changing? (one bit per sample) [Would be more useful at each cyle]
#		- Currently doing simple subtraction, but we could have a abs block after the subtraction
#       - If we could send the value of the subtraction back up we could use the filter block to filer positive elements
# 3- Correlation in a tricky way
#       Done, but need to show steve how I did it
#       Take away 
#           - Calculating the correlation is quite complex
#           - We can calulate the correlation using either 2 matrices of size (N) or 5 values
#           - 2 of those values can be cached to the next cycle
#           -> Instead of computing everything and ending up with one value, I ended up with 3 values
#              -> The rest of the math is done offline  
# 4 - Parity bit
#       Same as Sum of all values, but only submit 1 bit instead of 1 value