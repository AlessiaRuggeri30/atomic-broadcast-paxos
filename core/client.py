from utils import *
import sys

config = import_config(CONFIG_FILE)
network = create_network(config)

p_id = None
try:
    p_id = sys.argv[1]
except IndexError as error:
    print("You have to specify the process id as argument.")

client = Client(ip=network['clients']['ip'],
                port=network['clients']['port'],
                p_id=int(p_id),
                network=network)

client.run()
