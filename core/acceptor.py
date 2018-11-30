from utils import *
from paxos import *

config, MAX_NUM_ACCEPTORS = import_config(CONFIG_FILE)
network = create_network(config)
p_id = get_id()
if p_id < MAX_NUM_ACCEPTORS:
    acceptor = Acceptor(ip=network['acceptors']['ip'],
                        port=network['acceptors']['port'],
                        p_id=int(p_id),
                        network=network)

    acceptor.start()
else:
    print(f"The maximum number of acceptors allowed is {MAX_NUM_ACCEPTORS}, you can't create more.")
