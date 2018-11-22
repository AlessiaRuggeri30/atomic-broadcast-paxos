from classes import *
from utils import *

CONFIG_FILE = "config.txt"
LEADER = ""

config = import_config(CONFIG_FILE)
network = create_network(config)
