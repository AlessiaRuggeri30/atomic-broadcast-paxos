import sys


# ----------------------------------------------------------------------------------------------------
#
# UTILS FUNCTIONS
#
# ----------------------------------------------------------------------------------------------------

PRINTING = True


def greedy_leader_election(network):

    ''' Procedure to elect the leader'''

    p_id = network['proposers'][-1]
    return p_id


def import_config(config_file):
    config = []
    with open(config_file, 'r') as f:
        for line in f.readlines():
            if line != '':
                role, ip, port = line.strip('\n').split(' ')
                config.append([role, ip, port])
    return config


def create_network(config):
    network = {'clients': [], 'proposers': [], 'acceptors': [], 'learners': []}
    k = 0
    for agent in config:
        role, ip, port = agent[0], agent[1], int(agent[2])
        network[role] = {'ip': ip, 'port': port}
        k += 1
    return network


def print_stuff(msg):
    if PRINTING:
        print(msg)

