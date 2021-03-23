

# Testing Debugger Using Modelsim Through Docker

LeBug doesn't require using Docker to generate RTL. However, we do use Docker to run Modelsim, allowing users to test and build up on LeBug on Mac, Windows or Linux.

## Docker Basics

### Docker image vs. Container

- You can imagine that a container is an instance of an image
- A container is made from an image
- Multiple containers can be assigned to an image
- An image is a "snapshot" of a container

###Basic docker commands

- Show all images we have

  - ```docker images```

- Show all containers

  - ```docker ps --all``` 

- Copy a file

  - ```docker cp CONTAINER_NAME:/PATH/FILE.txt DESTINATION```
  - More information about it [here](<https://www.youtube.com/watch?v=7tGcnOvRQ9o>)

- Remove a container

  - ```docker rm CONTAINER_NAME_OR_ID```

- Remove image

  - ```docker rm IMAGE_NAME_OR_ID```

- Create a container from an image

  - ```docker run -it --name NEW_CONTAINER NAME IMAGE_NAME_OR_ID```

- Start/Stop a container

  - ```docker start CONTAINER_NAME_OR_ID``` 
    - To make it iterative: ```docker start -a CONTAINER_NAME_OR_ID``` OR
    - start a container normally and then run ```docker attach CONTAINER_NAME_OR_ID```
  - ```docker stop -t0 CONTAINER_NAME_OR_ID```

- Execute a single command on a container

  - ```docker exec CONTAINER_NAME_OR_ID YOUR_COMMAND```

    

## Using Modelsim on Docker 

We use the following Modelsim image used for docker:

- https://github.com/goldenSniperOS/modelsim-docker

Note that this image will automatically be downloaded when you try to run the "hw_test" on the examples folder. 

### Manually starting Modelsim

The instructions below are designed for Mac users, but commands for other operational systems should be fairly similar. Note that manually initializing the docker container is not needed in most scenarios.

- Initialize container
  - ```sudo docker run --net=host --env="DISPLAY"  -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix$DISPLAY  --volume="$HOME/.Xauthority:/root/.Xauthority:ro" --rm -it goldensniper/modelsim-docker```
- Create modelsim project
  - ```vlib work```
- Compile files
  - ```vlog debugProcessor.sv```
- Run modelsim and exit
  - ```vsim -c -do run -do exit testbench```

### Running a GUI on a container 

If you want to use the Modelsim GUI without using LeBug, you can do it with the following commands if you are using MacOS. Note, however, that LeBug automatically allows you to open the GUI of projects that you are running through our automated flow as discussed [here](Debugging&#32;the&#32;debugger.md).

- Step 1 - Open socat in your MacOS
  - ```socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\"```
- Step 2 - Start the container and attach to it
  - ```docker start modelsim```
  - ```docker attach modelsim```
- Step 3 - Export the right env variable inside the container
  - ```export DISPLAY=docker.for.mac.host.internal:0```
- Step 4 - Open the application

Note: Make sure to have xquarz installed and open in your mac. Also go to Settings -> security ->  Allow connections from network clients.