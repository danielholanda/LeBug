# Understanding and Writing Firmware

## Overview

The firmware is used to configure the instrumentation at debug time. When creating a firmware, you need to obey the following rules:

- All ISA instructions must be chained the same whay that the hardware is chained
- All chains must start with begin_chain() and must end with end_chain()

## Valid and End of Frame signal (EOF)

Most machine learning hardware implementations make extensive use of vectorization. LeBug taps into multiple values at the same time. This input vector is only observed by our instrumentation if the instrumentation input "valid" is high. This is a hardware-only signal and is abstracted away in the firmware.

Additionally, we also allow users to only perform some firmware instructions under certain conditions in the hardware. To allow this, our instrumentation has 2 end of frame signals (EOF). A high EOF signal indicates that the set of values we are observing just finished and next cycle will contain the next set of values. 

The user may, for example, decide to set the EOF signal high every time that we are done processing an image in a CNN. In this example, we may decide to do an operation only when we are done processing each image ("last"), or on the next valid signal after processing each image ("first"), or on every valid signal except when we are done processing each image ("notlast"), or on every valid signal exept the next valid signal after processing each image ("not first").

A better understanding of the EOF signal may be achieved by looking into the [firmware.py](https://github.com/danielholanda/LeBug/blob/master/src/firmware/firmware.py) file.

## Implemented Firmware

LeBug comes with a library of firmware code. Some examples of the firmware that has already been implemented includes:

- Distribution
- Summary Statistics (sparsity)
- Spatial Sparsity
- Vector Change
- Self Correlation
- Activation Predictiveness

Going over [those examples](https://github.com/danielholanda/LeBug/blob/master/src/firmware/firmware.py) might help better understanding how the firmware must be written.

## Examples

### Loopback

The simplest firmware possible is a loopback, in which all valid set of values received by the instrumentation are recorded.

```    python
def loopback(cp,N):   
    begin_chain() 
    v_commit(N)   # Send N values to data packer
    end_chain()
```

Expected results:

```    
********** Input vectors **********
Cycle 0:	[0.744 1.576 1.014 0.724 0.118 1.229 0.188 2.459]
Cycle 1:	[ 2.818 -0.083  1.959  0.644  0.84   2.628 -1.645 -1.564]
Cycle 2:	[-1.899  2.163  1.891  2.35   2.893  1.996  0.307  1.903]

********** Emulation results **********
[[ 0.744  1.576  1.014  0.724  0.118  1.229  0.188  2.459]
 [ 2.818 -0.083  1.959  0.644  0.84   2.628 -1.645 -1.564]
 [-1.899  2.163  1.891  2.35   2.893  1.996  0.307  1.903]]

********** Hardware results **********
[[ 0.744  1.576  1.014  0.724  0.118  1.229  0.188  2.459]
 [ 2.818 -0.083  1.959  0.644  0.84   2.628 -1.645 -1.564]
 [-1.899  2.163  1.891  2.35   2.893  1.996  0.307  1.903]]
```

### Cache and Mini Cache

Values can be "sent" from one chain to another either by storing values in the cache or mini cache. The firmware operations vv_add and all other VVALU operations implicily use the input vector as operator and the cache as the operand.

```    python
def minicache(cp):
    cp.begin_chain()
    cp.vv_add(0)      # Add the input vector to the vector stored in cache address 0
    cp.v_cache(0)     # Store the result in cache address 0
    cp.v_mc_save()    # Also save the result in the minicache
    cp.end_chain()

    cp.begin_chain()
    cp.v_mc_load()   # Use value in minicache instead of value in input vector
    cp.vv_add(0)     # Add the vector in the minicache to the vector stored in cache address 0
    cp.v_cache(0)    # Store the result in cache address 0
    cp.v_mc_save()   # Also save the result in the minicache
    cp.end_chain()

    cp.begin_chain()
    cp.v_mc_load()   # Use value in minicache instead of value in input vector
    cp.v_commit()    # Send N values to the data packer
    cp.end_chain()
    return cp.compile()
```

Expected results:

```    
********** Input vectors **********
Cycle 0:	[2 2 6 1 3 6 1 0]
Cycle 1:	[1 0 0 3 4 0 0 4]

********** Emulation results **********
[[ 4.  4. 12.  2.  6. 12.  2.  0.]
 [10.  8. 24. 10. 20. 24.  4.  8.]]

********** Hardware results **********
[[ 4  4 12  2  6 12  2  0]
 [10  8 24 10 20 24  4  8]]
```

### Distribution

A slightly more complex example is the distribution, in which a histogram is created. Note that the number of cycles that it takes to process each input vector of N samples is bins/M. The for loop is unrolled during compilation.

```    python
def distribution(cp,bins,M):
    assert bins%M==0, "Number of bins must be divisible by M"
    for i in range(int(bins/M)):       
        begin_chain()
        vv_filter(i)
        m_reduce('M')
        vv_add(i,'notfirst')
        v_cache(i)
        v_commit(M,'last')
        end_chain()
```

Expected results (form M=16):

```    
********** Input vectors **********
Cycle 0:	[6.268 2.575 2.042 4.962 6.475 3.808 8.827 6.163]
Cycle 1:	[4.328 3.529 3.089 6.561 3.947 0.537 3.582 6.642]


********** Emulation results **********
[[0. 0. 2. 1. 1. 0. 3. 0. 1. 0. 0. 0. 0. 0. 0. 0.]
 [1. 0. 0. 4. 1. 0. 2. 0. 0. 0. 0. 0. 0. 0. 0. 0.]]

********** Hardware results **********
[[0. 0. 2. 1. 1. 0. 3. 0. 1. 0. 0. 0. 0. 0. 0. 0.]
 [1. 0. 0. 4. 1. 0. 2. 0. 0. 0. 0. 0. 0. 0. 0. 0.]]
```

In this example, the FRU has been configured to store the numbers 0,1,2,3... This means that the first bin contains values greater than 0 and less or equal to 1, the second bin contains values greater than 1 and less or equal than 2 and so on.  

The 'notfirst' condition is used in the vv_add to reset each bi to zero every time we start a new frame. Frames are only commited to memory after each frame ends, by using the 'last' condition.

## Complete list of firmware instructions supported

The firmware instructions supported by the instrumentation is constantly evolving. For a complete list of the firmware instructions currently supported check out the [compiler source code](https://github.com/danielholanda/LeBug/blob/master/src/firmware/compiler.py).

