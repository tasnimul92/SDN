import os
import sys 
import time
import shlex, subprocess
import signal
import random
import threading

class SDNRand (threading.Thread):
  def __init__(self,protocol,target):
    threading.Thread.__init__(self)
    self.protocol=protocol
    self.target=target
  def run(self):

    while True:
      packet_size=random.randint(64,1048)
      packet_rate=random.randint(500,10000)
      number_packets=random.randint(1,150)
      ip=self.target
      port='80'
      x=self.protocol
      cmd = 'hping3 '+ip+' --'+str(x)+' -S -V -p 80 -i u'+str(packet_rate)+' -c '+str(number_packets)+' -d '+str(packet_size)                
      args = shlex.split(cmd)
      p = subprocess.Popen(args, shell=False) 
      time.sleep(2.0)
      # killing all processes in the group
      os.kill(p.pid, signal.SIGTERM)
      if p.poll() is None:  # Force kill if process
          os.kill(p.pid, signal.SIGKILL)

      r = random.randint(3,20)
      time.sleep(r-1)

x=sys.argv[1]
y= sys.argv[2]
protocol = SDNRand(x,y)
protocol.start()
