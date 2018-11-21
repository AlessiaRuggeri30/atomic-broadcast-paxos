import json
from multiprocessing import Process


# Agent and roles


class Agent(Process):

    ''' Generic class for paxos roles '''

    def __init__(self, role, ip, port):
        Process.__init__(self)
        self.role = role
        self.ip = ip
        self.port = port
        self.alive = True
        self.msgbox = Msgbox()
        self.counter = 0        # id of next sent message

    def __str__(self):
        return str((self.role, self.ip, self.port))

    def __repr__(self):
        return self.__str__()

    def run(self):

        ''' Wait for messages to handle '''

        pass

    def send_msg(self, m, receiver):

        # TODO IP multicast to receiver group
        pass

    def receive_msg(self, msg):
        self.msgbox.push(msg)

    def stop(self):
        self.alive = False


class Proposer(Agent):

    ''' Class representing proposer agent '''

    def __init__(self, role, ip, port):
        Agent.__init__(self, role="proposers")
        self.c_rnd = 0
        self.c_val = None
        self.v = 0

    def propose(self, ):
        pass

    def receive_msg(self, msg):
        pass


class Acceptor(Agent):

    ''' Class representing acceptor agent '''

    def __init__(self, role, ip, port):
        Agent.__init__(self, role="acceptors")
        self.rnd = 0
        self.v_rnd = 0
        self.v_val = None

    def receive_msg(self, msg):
        pass


class Learner(Agent):

    ''' Class representing learner agent '''

    def __init__(self, role, ip, port):
        Agent.__init__(self, role="learners")

    def receive_msg(self, msg):
        pass


# Handling messages

class Msg:

    ''' Class representing a message '''

    def __init__(self, phase, data):
        self.phase = phase
        self.data = data

    def encode(self):
        return json.dumps(vars(self))

    def decode(self, encoded):
        decoded = json.loads(encoded)
        self.phase, self.data = (decoded['phase'], decoded['data'])
        return self

    def __str__(self):
        return str((self.phase, self.data))
    # "c_rnd": c_rnd, "c_val": c_val, "rnd": rnd, "v_rnd": v_rnd, "v_val": v_val

    def fill_PHASE_1A(self, c_rnd):
        self.phase = "PHASE_1A"
        self.data = {"c_rnd": c_rnd}

    def fill_PHASE_1B(self, rnd, v_rnd, v_val):
        self.phase = "PHASE_1B"
        self.data = {"rnd": rnd, "v_rnd": v_rnd, "v_val": v_val}

    def fill_PHASE_2A(self, c_rnd, c_val):
        self.phase = "PHASE_2A"
        self.data = {"c_rnd": c_rnd, "c_val": c_val}

    def fill_PHASE_2B(self, v_rnd, v_val):
        self.phase = "PHASE_2B"
        self.data = {"v_rnd": v_rnd, "v_val": v_val}

    def fill_DECISION(self, v_val):
        self.phase = "DECISION"
        self.data = {"v_val": v_val}


class Msgbox:

    ''' Class representing the list of message that an agent received '''

    def __init__(self):
        self.received = []

    def push(self, msg):
        self.received.append(msg)

    def pop(self):
        return self.pop(0)























