from multiprocessing import Process
import socket
import json


# Agent and roles


class Agent(Process):

    ''' Generic class for paxos roles '''

    def __init__(self, role, ip, port):
        Process.__init__(self)
        self.role = role
        self.ip = ip
        self.port = port
        self.msgbox = Msgbox()
        self.counter = 0        # id of next sent message
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((ip, port))
        self.network = None

    def __str__(self):
        return str((self.role, self.ip, self.port))

    def __repr__(self):
        return self.__str__()

    def run(self):
        self.server.listen(10)
        print(f"Process ({self}) is listening")

        while True:
            conn, addr = self.server.accept()
            with conn:
                print(f"Process ({self}) connected by {addr}")
                encoded_msg = conn.recv(1024)
                if not encoded_msg:
                    break
                msg = Msg()
                msg.decode(encoded_msg)
                print(f"Process [{self}] received message of {msg.phase}")
                self.receive_msg(conn, msg)

    def send_msg(self, ip, port, msg):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            s.sendall(msg)

    def receive_msg(self, conn, msg):
        # to implement by subclasses
        pass

    def update_network(self, network):
        self.network = network


class Proposer(Agent):

    ''' Class representing proposer agent '''

    def __init__(self):
        Agent.__init__(self, role="proposers")
        self.c_rnd = 0
        self.c_val = None
        self.v = 0

    def propose_c_rnd(self):
        self.c_rnd += 1
        msg = Msg()
        msg.fill_PHASE_1A(self.c_rnd)
        msg_encoded = msg.encode()
        for acceptor in self.network['acceptors']:
            self.send_msg(acceptor.ip, acceptor.port, msg_encoded)
        pass

    def receive_msg(self, conn, msg):
        pass


class Acceptor(Agent):

    ''' Class representing acceptor agent '''

    def __init__(self, role, ip, port):
        Agent.__init__(self, role="acceptors")
        self.rnd = 0
        self.v_rnd = 0
        self.v_val = None

    def receive_msg(self, conn, msg):
        pass


class Learner(Agent):

    ''' Class representing learner agent '''

    def __init__(self, role, ip, port):
        Agent.__init__(self, role="learners")

    def receive_msg(self, conn, msg):
        pass


# Handling messages

class Msg:

    ''' Class representing a message '''

    def __init__(self, phase=None, data=None):
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
        return self.received.pop(0)























