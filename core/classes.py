from multiprocessing import Process
import socket
import struct
import json


# Handling messages

class Msg():

    ''' Class representing a message '''

    def __init__(self, phase=None, data=None):
        self.phase = phase
        self.data = data

    def encode(self):
        return json.dumps(vars(self)).encode()

    def decode(self, encoded):
        decoded = json.loads(encoded.decode())
        self.phase, self.data = (decoded['phase'], decoded['data'])
        return self

    def __str__(self):
        return str((self.phase, self.data))

    def fill_REQUEST(self, v, p_id=0):
        self.phase = "REQUEST"
        self.data = {"v": v, "id": p_id}

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


class Msgbox():

    ''' Class representing the list of message that an agent received '''

    def __init__(self):
        self.received = []

    def push(self, msg):
        self.received.append(msg)

    def pop(self):
        return self.received.pop(0)


# Agent and roles


class Agent(Process):

    ''' Generic class for paxos roles '''

    def __init__(self, role, ip, port, p_id):
        Process.__init__(self)
        self.role = role
        self.ip = ip
        self.port = port
        self.p_id = p_id
        self.msgbox = Msgbox()
        self.index = 0        # id of next sent message
        self.server = self.setup_server()
        self.client = self.setup_client()
        self.network = {}

    def __str__(self):
        return str((self.role, self.ip, self.port, self.p_id))

    def __repr__(self):
        return self.__str__()

    def setup_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 1))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, struct.pack('4sL',
                        socket.inet_aton(self.ip), socket.INADDR_ANY))
        return sock

    def setup_client(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.2)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 1))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, struct.pack('4sL',
                        socket.inet_aton(self.ip), socket.INADDR_ANY))
        return sock

    def run(self):
        self.server.bind((self.ip, self.port))
        print(f"Process ({self}) is listening")
        while True:
            encoded_msg, address = self.server.recvfrom(1024)
            msg = Msg()
            msg.decode(encoded_msg)
            self.receive_msg(msg)

    def send_msg(self, ip, port, msg):
        self.client.sendto(msg, (ip, port))

    def receive_msg(self, msg):
        # to implement by subclasses
        pass

    def update_network(self, network):
        self.network = network


class Client(Agent):
    def request(self, v):
        msg = Msg()
        msg.fill_REQUEST(v)
        msg_encoded = msg.encode()
        self.send_msg(self.network['proposers'][0], msg_encoded)


class Proposer(Agent):

    ''' Class representing proposer agent '''

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, role="proposers", *args, **kwargs)
        self.c_rnd = 0
        self.c_val = None
        self.v = 0

    def prepare(self, v):
        self.v = v
        self.c_rnd += 1
        msg = Msg()
        msg.fill_PHASE_1A(self.c_rnd)
        msg_encoded = msg.encode()
        for acceptor in self.network['acceptors']:
            self.send_msg(acceptor.ip, acceptor.port, msg_encoded)
        pass

    def receive_msg(self, msg):
        pass


class Acceptor(Agent):

    ''' Class representing acceptor agent '''

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, role="acceptors", *args, **kwargs)
        self.rnd = 0
        self.v_rnd = 0
        self.v_val = None

    def receive_msg(self, msg):
        pass


class Learner(Agent):

    ''' Class representing learner agent '''

    def receive_msg(self, msg):
        pass

























