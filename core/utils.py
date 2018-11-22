from classes import *


def greedy_leader_election(network):

    ''' Procedure to elect the leader'''

    global LEADER
    p_id = network['proposers'][-1]
    LEADER = p_id


def import_config(config_file):
    config = []
    with open(config_file, 'r') as f:
        for line in f.readlines():
            role, ip, port = line.strip('\n').split(' ')
            config.append([role, ip, port])
    return config


def create_network(config):
    network = {'clients': [], 'proposers': [], 'acceptors': [], 'learners': []}
    k = 0
    for agent in config:
        role, ip, port = agent[0], agent[1], int(agent[2])
        a = Agent(role, ip, port, p_id=k)
        network[a.role].append(a)
        k += 1

    for role in ['clients', 'proposers', 'acceptors', 'learners']:
        for agent in network[role]:
            agent.update_network(network)



