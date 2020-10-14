# Documentation

This first version of the documentation explains the basics of how to get started generating RTL instrumentation that can be emulated or simulated.

## Understanding how it works



<img src="img/sample_hw.png" alt="drawing" width="300"/>

#### Bulding Blocks

The debug processor can be composed out of the following building blocks:

- **Input Buffer** (N,IB_DEPTH)
  - **Description:** Stores IB_DEPTH tensors while other tensors are still being processed
  - **ISA instructions:** None
- **Filter Unit** (N,M,FUVRF_SIZE) 
  - **Description:** For each of the N elements received, output M elements. Each of those M elements is a binary indicator of wether the value is within a certain range. All ranges are stored in the fu_mem and the same range is applies to all elements of the input vector N.
  - **ISA instructions: ** vv_filter(addr)
- **Matrix Vector Reduce** (N,M) 
  - **Description:** This block receives a N*M input and reduces the result either in the M or N axis. The only type of reduction that is currently made is the sum. This block is mandatory when the filter unit is instantiated.
  - **ISA instructions: ** m_reduce(axis)
- **Vector Scalar Reduce** (N) 
  - **Description:** Reduce values along a given axis and output either 1, M or N values
  - **ISA instructions: **v_reduce
- **Vector Vector ALU** (N,VVVRF_SIZE) 
  - **Description:** Performs basic vector-vector operations and offers the option to store things in a scratchpad.
  - **ISA instructions: **vv_add(addr), vv_mul(addr), vv_sub(addr), v_cache(addr)
- **Data Packer** (N,M)
  - **Description:** Receives 1, N or M values and sends it to the trace buffer N at a time
  - **ISA instructions: ** None
- **Trace Buffer** (N,TB_SIZE)
  - **Description:** Circular Trace Buffer
  - **ISA instructions: ** None

#### Parameters

Every time that the we emulate the processor or create RTL for it, we have to define the following parameters:

- **N**: Input tensor width
- **M:** Number of binary ranges that will be avaluated by the filter unit (M<=N)
- **IB_DEPTH:** Number of tensors we can store in the input buffer
- **FUVRF_SIZE:** Number of different ranges we can have for the FIlter Unit (VRF size is FUVRF_SIZE*M)
- **VVVRF_SIZE:** Number of tensors we can store in the vector-vector scratchpad of the Filter Unit
- **TB_SIZE:** Number of tensors we can store in the trace buffer
- **DATA_WIDTH**: Input/output data width
- **MAX_CHAINS:** Maximum number of firmware chains the hardware is able to execute.

#### Firmware

The firmware is used to configure the instrumentation at debug time. When creating a firmware, you need to obey the following rules:

- All ISA instructions must be chained the same whay that the hardware is chained
- All chains must start with begin_chain() and must end with end_chain()
- All ISA instructions may also receive a condition that enables/disables this operation according to the "end of frame" signal. Those conditions may be "first", "notfirst", "last", and "notlast".

So far, we our list of firmware includes:

- Distribution
- Summary Statistics (sum)
- Spatial Sparsity
- Vector Change
- Self Correlation
- Invalid values

**Example:**

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



## Running it for the first time

### Testing the emulator

Simply cd into examples/minimal and run 'python3 test_emulator'

### Simulation with iVerilog

Simulation with Icarus Verilog is not recommended, as we use system Verilog, which is not supported by his tool.

To simulate using iverilog use the command:

```iverilog -g2012 -s testbench -o debugProcessor debugProcessor.sv```

followed by 

```vvp debugProcessor```

### Configuring a new example

Each example is composed of those main files:

- Config.yaml file
  - Configures the parameters that determine the architecture at compile time
  - Configures initial firmware loaded in the design
- Main python file
  - Initializes the processor using either emulatedHw class or rtlHw class
  - After initializing the processor, all inputs functions that interact with the processor should be supported by both emulator and rtlHw

## Functions supported by both emulatedHw and rtlHw

- config()
  - Sets up run-time parameters including
    - Firmware
    - Memory initializations
- run()
  - Starts either simulation or emulation
  - Returns results from simulation/emulation
- compiler
  - Shoudl be able to handle all ISA instructions and compile() at the end

