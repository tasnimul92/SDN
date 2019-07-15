from __future__ import division
import requests
from requests.auth import HTTPBasicAuth
import json
import sys
import time
import subprocess
import threading 
import numpy as np
import random
import pickle
import os.path
import copy

#SVM libs
import numpy as np
from numpy import linalg
import pylab as pl


eps = 0.8 # using epsilon greedy policy with probability 0.2  ; this means the algorithm will take 20% random action and 80% the best action from the experience
actions=list(range(0,9))  # actions are matchfield numbers ranged from 0 to 10 according to openflow sepcification
gamma = 0.6 #discount factor
alpha=0.8 #learning rate  

sendState = []
Switches_Status = {}
response = {}
#Comment here
if os.path.isfile("qtableE-8.txt"):
    with open("qtableE-8.txt", "rb") as fp:   # Unpickling if the q_table is already created
   		 q_table = pickle.load(fp)
    fp.close()
else:
    q_table = dict() #initializing q table empty as a dictionary
    

#Comment here
class postmatchfield:
  p=[]
  postheader= {'Accept':'application/json'}
  getheader = {'Content-Type':'application/json' , 'Accept':'text/html'}
  def __init__(self,action):
     parameters="matchfields.json"  # all the matchfield combinations are in this file
     with open(parameters, 'r') as filehandle:  
			for line in filehandle:
				self.p.append(line)
     fieldToDelete=self.p[action] # actions start from 1 and list start from 0  				                     	       	  
     flowdelete = requests.delete('http://127.0.0.1:8181/onos/v1/flows/application/org.onosproject.fwd', auth=('onos', 'rocks'), headers=self.postheader)
     response = requests.post('http://127.0.0.1:8181/onos/v1/configuration/org.onosproject.fwd.ReactiveForwarding?preset=false', data=fieldToDelete, auth=('onos', 'rocks'), headers=self.getheader)





#---------------------------------------------------------------------#
class StatsCollector(threading.Thread):
    global sendState, Switches_Status,response
    deviceids=[]
	
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.getheader = {'Content-Type':'application/json' , 'Accept':'text/html'}
        self.postheader= {'Accept':'application/json'}
        deviceresponse=  requests.get('http://127.0.0.1:8181/onos/v1/devices', auth=HTTPBasicAuth('onos', 'rocks')).json()
        for x in deviceresponse:
             for p in deviceresponse[x]:
                  self.deviceids.append(str(p['id']))

                  
    def run(self):
        global sendState, Switches_Status,response
        f2 = 0
        f1 = 0
        t_ob = 3.0
        count=0.0
        while True:                    
            count=count+1.0
            for i in self.deviceids:
                url = 'http://127.0.0.1:8181/onos/v1/flows/' + i
                headers  = {"Accept": "application/json"}
                response = requests.get(url, headers = headers, auth=HTTPBasicAuth('karaf', 'karaf'))
                if response.json().has_key('flows'):
                    f2 = len(response.json()['flows'])

                    with open('flows.txt', 'a+') as files:
                         files.write(str(count)+","+str(f2)+ "\n")
                         files.close()
                    deltaf = abs(f2 -f1)
                    
                    f1 = f2

                    sendState=[f2,deltaf]
                else:
                    print 'StatsCollector | ',i,' has no flows'

            #print Switches_Status
            time.sleep(t_ob)
#---------------------------------------------------------------------#


#---------------------------------------------------------------------#
class QLearning(threading.Thread):
    global sendState

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global sendState    #made global here
        currentState=list()
        itercount = 0
        iterations = 0
        while True:

            if len(sendState) == 0:
                 continue
            else:
                        #print sendState
                itercount = itercount + 1
                if itercount == 0:
                    currentState=[sendState[0],sendState[1]]
                else:
                    action=choose_action(currentState)
                    #print 'act' , action
                    #postmatchfield(action)
                    #time.sleep(8.0)
                    reward=get_reward(sendState[0])
                    #print reward
                    next_usable_state=[sendState[0],sendState[1]]
                    #print(next_usable_state)
                    q(currentState)[action] = q(currentState, action) + alpha * (reward + gamma *  np.max(q(next_usable_state) - q(currentState, action)))
                    with open('qtableE-8.txt', 'w') as files:
                       pickle.dump(q_table, files)
                    currentState = copy.deepcopy(next_usable_state)
                    #print 'itercount', itercount, 'action' , action , 'state' , sendState
                    if itercount == 100:
                        iterations = iterations + 100
                        with open('rewards.txt', 'a+') as files:
                            files.write(str(iterations) + "," + str(reward) + "\n")
                            files.close()
                        print 'Total '+  str(iterations) + ' iterations have finished and the immediate reward is ' + str(reward)
                        itercount = 0
            time.sleep(10.0)
            #print 'slept'


def choose_action(current_state):
    #print 'act', current_state
    if random.uniform(0, 1) < eps:
        return random.choice(actions) 
    else:
        return np.argmax(q(current_state))

def q(state, action=None):
    state=tuple(state)
    if state not in q_table:
        q_table[state] = np.zeros(len(actions))
        
    if action is None:
        return q_table[state]
    
    return q_table[state][action]  
        
def get_reward(next_state):
    criteria = list()
    for x in response.json():            
         for p in response.json()[x]:
              j=p['selector']['criteria']
              for i in j:
                  criteria.append(len(j))
                      
    immediate_reward =  (sum(criteria)/len(criteria))
    if next_state < 3000 :
        reward = immediate_reward
    else:
        reward = 0
    return reward 
#---------------------------------------------------------------------#


#Main Program
#----------------------------------------------#



Stats = StatsCollector("StatsCollector")
QLearning = QLearning("QLearning")

Stats.start()
QLearning.start()

