#!/usr/bin/env python
from utils import *
from classes import *

MAX_NUM_ACCEPTORS = 3       # if you want more acceptors, change here


def client(network, p_id):

    """ Create a client from the network and run it.

        :param network: dict
            The network containing processes info.
        :param p_id: int
            The process id of the created client.
    """

    # print('-> client ', p_id)
    client = Client(ip=network['clients']['ip'],
                    port=network['clients']['port'],
                    p_id=int(p_id),
                    network=network)

    client.run()
    # print('client done.')


def proposer(network, p_id):

    """ Create a proposer from the network and run it.

        :param network: dict
            The network containing processes info.
        :param p_id: int
            The process id of the created proposer.
    """

    # print('-> proposer', p_id)
    proposer = Proposer(ip=network['proposers']['ip'],
                        port=network['proposers']['port'],
                        p_id=int(p_id),
                        network=network)

    proposer.max_num_acceptors = MAX_NUM_ACCEPTORS

    proposer.start()


def acceptor(network, p_id):

    """ Create an acceptor from the network and run it.

        :param network: dict
            The network containing processes info.
        :param p_id: int
            The process id of the created acceptor.
    """

    # print('-> acceptor', p_id)
    acceptor = Acceptor(ip=network['acceptors']['ip'],
                        port=network['acceptors']['port'],
                        p_id=int(p_id),
                        network=network)

    acceptor.start()


def learner(network, p_id):

    """ Create a learner from the network and run it.

        :param network: dict
            The network containing processes info.
        :param p_id: int
            The process id of the created learner.
    """

    # print('-> learner ', p_id)
    learner = Learner(ip=network['learners']['ip'],
                      port=network['learners']['port'],
                      p_id=int(p_id),
                      network=network)

    learner.max_num_acceptors = MAX_NUM_ACCEPTORS

    learner.start()


if __name__ == '__main__':
    CONFIG_FILE = sys.argv[1]
    role = sys.argv[2]
    p_id = int(sys.argv[3])

    config = import_config(CONFIG_FILE)
    network = create_network(config)

    if role == 'acceptor':
        rolefunc = acceptor
    elif role == 'proposer':
        rolefunc = proposer
    elif role == 'learner':
        rolefunc = learner
    elif role == 'client':
        rolefunc = client
    rolefunc(network, p_id)
