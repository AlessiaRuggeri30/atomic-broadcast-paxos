from utils import *
from classes import *

config, MAX_NUM_ACCEPTORS = import_config(CONFIG_FILE)
network = create_network(config)
p_id = get_id()

learner = Learner(ip=network['learners']['ip'],
                  port=network['learners']['port'],
                  p_id=int(p_id),
                  network=network)

learner.start()
