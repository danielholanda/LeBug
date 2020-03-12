from emulator import *

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


# Ideas for new instruments:
# - Check elements that are between -inf and min_range OR NaN OR between max_range and Inf (given a specific activation)
# - How often is the entire vector changing? (one bit per sample) [Would be more useful at each cyle]
#		First vector - Save to memory addr0
#		All other 
#			Chain1
#				Subtract saved and current value
#				Save subtracted value to addr2
#			Chain2
#				Save original value to addr0
#			Chain3
#				Reduce subtracted value (reduce must be after ALU)
#				Commit 1
# Correlation in a tricky way
# https://www.investopedia.com/terms/c/correlation.asp