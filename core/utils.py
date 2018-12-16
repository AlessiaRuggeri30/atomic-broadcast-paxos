# ----------------------------------------------------------------------------------------------------
#
# UTILS FUNCTIONS
#
# ----------------------------------------------------------------------------------------------------

PRINTING = False


def greedy_leader_election(network):

    """ Procedure to elect the leader of Paxos instances.

        :param network: dict
            The network of processes divided by roles.
        :return: int
            The process id (p_id) of the leader.
    """

    p_id = network['proposers'][-1]
    return p_id


def import_config(config_file):

    """ Import and parse the config file in order to convert it to a list.

        :param config_file: str
            The name of the config file.
        :return: list
            The list containing info about processes in the config file.
    """

    config = []
    with open(config_file, 'r') as f:
        for line in f.readlines():
            if line != '':
                role, ip, port = line.strip('\n').split(' ')
                config.append([role, ip, port])
    return config


def create_network(config):

    """ Convert config list to a network dictionary where the processes are divided by roles.

        :param config: list
            The list create using the config file.
        :return: dict
            The dictionary containing a network of processes divided by roles.
    """

    network = {'clients': [], 'proposers': [], 'acceptors': [], 'learners': []}
    k = 0
    for agent in config:
        role, ip, port = agent[0], agent[1], int(agent[2])
        network[role] = {'ip': ip, 'port': port}
        k += 1
    return network


def print_stuff(msg):

    """ It just allow to easily insert or eliminate the prints """

    if PRINTING:
        print(msg)

