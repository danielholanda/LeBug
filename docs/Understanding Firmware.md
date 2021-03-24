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
- Summary Statistics (sum)
- Spatial Sparsity
- Vector Change
- Self Correlation
- Invalid values

Going over [those examples](https://github.com/danielholanda/LeBug/blob/master/src/firmware/firmware.py) might help better understanding how the firmware must be written.

## Examples

### Loopback

The simplest firmware possible is a loopback, in which all valid set of values received by the instrumentation are recorded.

```    python
def loopback(cp,N):   
    begin_chain()
    v_commit(N)
    end_chain()
```

Expected results:

```    python
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

### Distribution

A slightly more complex example is the distribution, in which a histogram is created 

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

Expected results:

```    python
...
```

### 

