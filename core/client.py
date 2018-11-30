from utils import *
from paxos import *

config, MAX_NUM_ACCEPTORS = import_config(CONFIG_FILE)
network = create_network(config)
p_id = get_id()

client = Client(ip=network['clients']['ip'],
                port=network['clients']['port'],
                p_id=int(p_id),
                network=network)

client.run()
