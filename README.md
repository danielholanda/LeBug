# LeBug

LeBug is an open-source debug instrumentation that allows for the live debugging of machine learning systems during training. Different from previous debug instrumentation, our instrumentation offers firmware programmability, allowing the researcher to gather data in a large variety of ways that would likely not be anticipated at compile time.

The manuscript related to LeBug is to appear at [The 29th IEEE International Symposium On Field-Programmable Custom Computing Machines (FCCM 2021)](https://www.fccm.org/).

<img src="img/overview.png" alt="drawing" width="400"/>

## Installing dependencies

### Testing your installation

- To test your installation, go into the examples/minimal directory and run
    ``` 
    python3 test_emulator
    ```

## Getting Started

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

## Contents:
- src -- includes source code for LeBug
- test -- simple examples that be run to test the tool
- examples -- complex examples that can take a significant amount of time to run 
- docs -- additional documentation on this repository

## Authors

* **Daniel Holanda Noronha** - *danielhn-at-ece.ubc.ca* 
* **Zhiqiang Que**
* **Wayne Luk**
* **Steve Wilton**

## Citing LeBug

Please cite LeBug in your publications if it helps your research work:

```
@INPROCEEDINGS{LeBug,
     author = {{Holanda Noronha}, D. and {Que}, Z. and {Luk}, W. and {Wilton}, S.~J.~E.},
     booktitle={2021 IEEE 29th Annual International Symposium on Field-Programmable Custom Computing Machines (FCCM)}, 
     title = "{Flexible Instrumentation for Live On-Chip Debug of Machine Learning Training on FPGAs}",
     year = {2021}
} 
```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details