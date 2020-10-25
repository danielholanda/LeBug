# This files contains some of the different firmware that can be used by the HW and emulator

# Firmware for a distribution with multiple sets of N values
def distribution(cp,bins,M):
    assert bins%M==0, "Number of bins must be divisible by M for now"
    for i in range(int(bins/M)):
        cp.begin_chain()
        cp.vv_filter(i)
        cp.m_reduce('M')
        cp.vv_add(i,'notfirst')
        cp.v_cache(i)
        cp.v_commit(M,'last')
        cp.end_chain()
    return cp.compile()

# Summary statistics - Number of non-sparse elements
def summaryStats(cp):
    # Remember to properly initialize fu.vrf

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

# Calculate spatial sparsity
def spatialSparsity(cp,N):
    # Remember to properly initialize fu.vrf
    cp.begin_chain()
    cp.vv_filter(0)
    cp.m_reduce('N')
    cp.v_commit(N)
    cp.end_chain()
    return cp.compile()

# Check if previous vector changed
def vectorChange(cp):

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

# Self correlation with the previous sample
def correlation(cp):

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

# Check if previous vector changed
def passThrough(cp):
    cp.begin_chain()
    cp.end_chain()
    return cp.compile()

# Sum all input values
def sumAll(cp):
    cp.begin_chain()
    cp.v_reduce()
    cp.v_commit(1)
    cp.end_chain()
    return cp.compile()

# Raw values
def raw(cp):
    cp.begin_chain()
    cp.v_commit()
    cp.end_chain()
    return cp.compile()

# Simple test for vvalu
def vvalu_simple(cp):
    cp.begin_chain()
    cp.vv_add(0)
    cp.v_cache(0)
    cp.v_commit()
    cp.end_chain()
    return cp.compile()

# Simple test for fru
def fru_simple(cp):
    cp.begin_chain()
    cp.vv_filter(0)
    cp.m_reduce('M')
    cp.v_commit()
    cp.end_chain()
    return cp.compile()

# Ideas for new instruments:
# 1- Check elements that are between -inf and min_range OR NaN OR between max_range and Inf (given a specific activation)
#   In the previous instrumentation, I would need one instrument for each of them (3x more memory)
# 2- How often is the entire vector changing? (one bit per sample) [Would be more useful at each cyle]
#       - Currently doing simple subtraction, but we could have a abs block after the subtraction
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