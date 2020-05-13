

## Instructions on how to interface with Modelsim docker image

You can find details on the container at this website:

- https://github.com/goldenSniperOS/modelsim-docker

### Commands to run:

- Initialize container
  - ```sudo docker run --net=host --env="DISPLAY"  -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix$DISPLAY  --volume="​$HOME/.Xauthority:/root/.Xauthority:ro" --rm -it goldensniper/modelsim-docker```
- Create modelsim project
  - ```vlib work```
- Compile files
  - ```vlog debugProcessor.sv```
- Run modelsim and exit
  - ```vsim -c -do run -do exit testbench```



## Docker image vs. Container

- You can imagine that a container is an instance of an image
- A container is made from an image
- Multiple containers can be assigned to an image
- An image is a "snapshot" of a container

## Basic docker commands

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

    

  