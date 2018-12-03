from utils import *
from classes import *

config, MAX_NUM_ACCEPTORS = import_config(CONFIG_FILE)
network = create_network(config)
p_id = get_id()

proposer = Proposer(ip=network['proposers']['ip'],
                    port=network['proposers']['port'],
                    p_id=int(p_id),
                    network=network)

proposer.max_num_acceptors = MAX_NUM_ACCEPTORS
if proposer.p_id == 0:
    proposer.leader = True

proposer.start()
