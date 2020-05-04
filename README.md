# Documentation

This first version of the documentation explains the basics of how to get started generating RTL instrumentation that can me emulated or simulated.

### Testing the emulator

Simply cd into examples/minimal and run 'python test_emulator'



### Configuring a new example

Each example is composed of those main files:

- Config.yaml file
  - Configures the parameters that determine the architecture at compile time
  - Configures initial firmware loaded in the design
- Main python file
  - Initializes the processor using either emulatedHw class or rtlHw class
  - After initializing the processor, all inputs functions that interact with the processor should be supported by both emulator and rtlHw

## Functions supported by both emulatedHw and rtlHw

- compiler()
  - Initializes the compiler
- config()
  - Sets up run-time parameters including
    - Firmware
    - Memory initializations
- run()
  - Starts either simulation or emulation
  - Returns results from simulation/emulation

