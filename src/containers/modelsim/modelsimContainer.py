import docker, subprocess, sys

class modelsimContainer():

    # Run a given command using subprocess (useful for when the API is not enough)
    def runSubprocess(self,cmd,log=True):
        proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        proc.wait()
        # Print results
        result = proc.stdout.readlines()+proc.stderr.readlines()
        if self.log and log:
            [ print(r.decode("utf-8"), end = '') for r in result]
        return result

    # Clean all logs from container to avoid files from accumulating
    def cleanLog(self):
        # Current script only works for MacOs
        if sys.platform=='darwin':
            log_path=self.runSubprocess(['docker','inspect','--format=\'{{.LogPath}}\'','modelsim'],log=False)[0].decode("utf-8")
            self.runSubprocess(['bash','-c',"docker run -it --rm --privileged --pid=host alpine:latest nsenter -t 1 -m -u -n -i -- truncate -s0 "+log_path])

    # Execute a command on a running container
    def exec(self,cmd):
      exec_log=self.apiClient.exec_start(self.apiClient.exec_create(self.container.name, cmd))
      if self.log:
          print(exec_log.decode("utf-8"))

    # Copy files to/from container
    def copy(self,src,dst):
      self.runSubprocess(['docker','cp',src,dst])

    # Start container
    def start(self):
        self.container.start()

    # Stop container
    def stop(self): 
        self.container.stop(timeout=0)
        self.cleanLog()

    def __init__(self,log):
        # Start docker dockerClient
        self.dockerClient = docker.from_env()
        self.apiClient = docker.APIClient(base_url='unix://var/run/docker.sock')
        self.log=log

        # Check whether we already have the container
        try:
            self.container = self.dockerClient.containers.get('modelsim')
        # If we don't, download it
        except: 
            print("Downloading modelsim image - This might take 5-10min")
            dockerClient.containers.run('goldensniper/modelsim-docker',stdin_open = True, tty = True,detach=True,name='modelsim')
            self.container = dockerClient.containers.get('modelsim')
            print("Download complete")

modelsim = modelsimContainer(log=True)
modelsim.start()
modelsim.copy('debugProcessor.sv','modelsim:/debugProcessor.sv')
modelsim.copy('inputBuffer.sv','modelsim:/inputBuffer.sv')
modelsim.exec('vlib work')
modelsim.exec('vlog debugProcessor.sv')
modelsim.exec('vsim -c -do "run -all" testbench')
modelsim.copy('modelsim:/simulation_results.txt','simulation_results.txt')
modelsim.stop()
