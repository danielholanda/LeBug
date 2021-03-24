# Debugging the Debugger

LeBug uses a Docker container to test the generated RTL when using different firmware. When modifying source files, errors might occur in the container and the root-cause of the problem will not be shown outside of the container. This document describes how to have better visibility into the computation that happens inside the container.



## Visualizing Modelsim compilation messages

After instantiating the rtlHw class, the user is able to insert sample input vectors to be tapped by the instrumentation. Those input vectors are mapped into a testbench used to test the generated.

``` python
# Instantiate rltHw
hw_proc  = rtlHw(N,M,IB_DEPTH,FUVRF_SIZE,VVVRF_SIZE,TB_SIZE,DATA_WIDTH,MAX_CHAINS,DATA_TYPE,DEVICE_FAM)

# Create a set of N random inputs
input_vector = np.random.randint(5, size=N)

# Add the random inputs as inputs in the testbench
eof=False
hw_proc.push([input_vector,eof])
```

Once the hardware has been generated, the command run() may be used to test the hardware on Modelsim. A useful optional argument for the run() function is "log", which shows the entire compilation process of Modelsim on the screen, including possible compilation errors.

``` python
# Generate RTL and start tests on Modelsim with logging mode enabled
hw_results = hw_proc.run(steps=50,log=True)
```



## Enabling Modelsim GUI through Docker

LeBug also allows the option to open the Modelsim GUI through Docker for better debugging.

``` python
# Generate RTL and start tests on Modelsim and open GUI
hw_results = hw_proc.run(steps=50,gui=True)
```

For more information about this setup, please see our documentation on [Testing our debugger using Modelsim through Docker](Modelsim&#32;on&#32;Docker.md).

