import json

from core.classes import *

LEADER = ""


def leader_election():

    ''' Procedure to elect the leader'''

    global LEADER
    # LEADER =
    pass


# Read config.json
with open('config.json', 'r') as f:
    config = json.load(f)

# Write back to config.json
# with open('config.json', 'w') as f:
#     json.dump(config, f)


def create_m(phase, c_rnd=None, c_val=None, rnd=None, v_rnd=None, v_val=None):
    if phase in ["1A", "1B", "2A", "2B", "DECISION"]:
        return {"phase": phase, "c_rnd": c_rnd, "c_val": c_val, "rnd": rnd, "v_rnd": v_rnd, "v_val": v_val}


proposer = Proposer(1)

acceptor = Acceptor(1)

m = create_m("1A", c_rnd=4)
msg = proposer.send_msg(m, acceptor)
acceptor.receive_msg(msg)
print(acceptor.msgbox.pop().read())




