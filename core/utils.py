import sys

CONFIG_FILE = "config.txt"


# ----------------------------------------------------------------------------------------------------
#
# UTILS FUNCTIONS
#
# ----------------------------------------------------------------------------------------------------


def greedy_leader_election(network):

    ''' Procedure to elect the leader'''

    p_id = network['proposers'][-1]
    return p_id


def import_config(config_file):
    config = []
    k = 0
    MAX_NUM_ACCEPTORS = 3
    with open(config_file, 'r') as f:
        for line in f.readlines():
            if k < 4:
                role, ip, port = line.strip('\n').split(' ')
                config.append([role, ip, port])
            else:
                _, value = line.strip('\n').split(' ')
                MAX_NUM_ACCEPTORS = int(value)
            k += 1
    return config, MAX_NUM_ACCEPTORS


def create_network(config):
    network = {'clients': [], 'proposers': [], 'acceptors': [], 'learners': []}
    k = 0
    for agent in config:
        role, ip, port = agent[0], agent[1], int(agent[2])
        network[role] = {'ip': ip, 'port': port}
        k += 1
    return network


def get_id():
    p_id = None
    try:
        p_id = sys.argv[1]
    except IndexError:
        print("You have to specify the process id as argument.")
    return int(p_id)
