import json

from core.classes import *

CONFIG_FILE = "config.txt"
LEADER = ""


def leader_election():

    ''' Procedure to elect the leader'''

    global LEADER
    # LEADER =
    pass


config = []
with open(CONFIG_FILE, 'r') as f:
    for line in f.readlines():
        role, ip, port = line.strip('\n').split(' ')
        config.append([role, ip, port])

print(config)

network = {'clients': [], 'proposers': [], 'acceptors': [], 'learners': []}
for agent in config:
    a = Agent(agent[0], agent[1], agent[2])
    network[a.role].append(a)

print(network)




