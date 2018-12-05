from threading import Thread
import socket
import struct
import json
import math
from utils import print_stuff


# ----------------------------------------------------------------------------------------------------
#
# HANDLING MESSAGES
#
# ----------------------------------------------------------------------------------------------------


class Msg():

    ''' Class representing a message '''

    def __init__(self, instance=None, phase=None, data=None):
        self.instance = instance
        self.phase = phase
        self.data = data

    def encode(self):
        return json.dumps(vars(self)).encode()

    def decode(self, encoded):
        decoded = json.loads(encoded.decode())
        self.instance, self.phase, self.data = (decoded['instance'], decoded['phase'], decoded['data'])
        return self

    def __str__(self):
        return str((self.instance, self.phase, self.data))

    def fill_REQUEST(self, v):
        self.phase = "REQUEST"
        self.data = {"v": v}

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


# ----------------------------------------------------------------------------------------------------
#
# AGENTS AND ROLES
#
# ----------------------------------------------------------------------------------------------------


class Agent(Thread):

    ''' Generic class for paxos roles '''

    def __init__(self, role, ip, port, p_id, network):
        Thread.__init__(self)
        self.role = role
        self.ip = ip
        self.port = port
        self.p_id = p_id
        self.server = self.setup_server()
        self.client = self.setup_client()
        self.network = network

    def __str__(self):
        return str((self.role, self.ip, self.port, self.p_id))

    def __repr__(self):
        return self.__str__()

    def create_state(self, instance):
        # to be implemented by subclasses
        pass

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
        print_stuff(f"{self} is listening")
        while True:
            encoded_msg, address = self.server.recvfrom(1024)
            msg = Msg()
            msg.decode(encoded_msg)
            self.receive_msg(msg)

    def send_msg(self, ip, port, msg):
        self.client.sendto(msg, (ip, port))

    def receive_msg(self, msg):
        # to be implemented by subclasses
        pass


class Client(Agent):

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, role="clients", *args, **kwargs)
        self.num_instance = 0

    def run(self):
        while True:
            v = input("Request's value: ")
            self.request(v)

    def request(self, v):
        msg = Msg()
        msg.fill_REQUEST(v)
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends request msg {msg} to proposers")
        self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)


class Proposer(Agent):

    ''' Class representing proposer agent '''

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, role="proposers", *args, **kwargs)
        self.states = {}
        self.leader = False
        self.num_instance = 0
        self.max_num_acceptors = 3

    def create_state(self, instance):
        if instance not in self.states:
            self.states[instance] = {"c_rnd": 0, "c_val": None, "v": None,
                                     "max_v_rnd": 0, "max_v_val": 0,
                                     "quorum1B": 0, "quorum2B": 0}

    def phase_1A(self, instance):
        self.states[instance]['c_rnd'] = 1 * self.p_id
        msg = Msg(instance)
        msg.fill_PHASE_1A(self.states[instance]['c_rnd'])
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends msg {msg} to acceptors")
        self.send_msg(self.network['acceptors']['ip'], self.network['acceptors']['port'], msg_encoded)

    def phase_2A(self, instance, data):
        if data['rnd'] == self.states[instance]['c_rnd']:
            self.states[instance]['quorum1B'] += 1
        print_stuff(self.states[instance]['max_v_rnd'])
        if data['v_rnd'] >= self.states[instance]['max_v_rnd']:
            self.states[instance]['max_v_rnd'] = data['v_rnd']
            self.states[instance]['max_v_val'] = data['v_val']
        if self.states[instance]['quorum1B'] >= math.ceil((self.max_num_acceptors+1) / 2):  # if it has quorum of acceptors
            self.states[instance]['quorum1B'] = 0  # reset quorum
            if self.states[instance]['max_v_rnd'] == 0:
                self.states[instance]['c_val'] = self.states[instance]['v']
            else:
                self.states[instance]['c_val'] = self.states[instance]['max_v_val']

            msg = Msg(instance)
            msg.fill_PHASE_2A(self.states[instance]['c_rnd'], self.states[instance]['c_val'])
            msg_encoded = msg.encode()
            print_stuff(f"{self} sends msg {msg} to acceptors")
            self.send_msg(self.network['acceptors']['ip'], self.network['acceptors']['port'], msg_encoded)

    def decide(self, instance, data):
        if data['v_rnd'] == self.states[instance]['c_rnd']:
            self.states[instance]['quorum2B'] += 1
        if self.states[instance]['quorum2B'] >= math.ceil((self.max_num_acceptors+1) / 2):
            self.states[instance]['quorum2B'] = 0  # reset quorum

            msg = Msg(instance)
            msg.fill_DECISION(self.states[instance]['c_val'])
            msg_encoded = msg.encode()
            print_stuff(f"{self} sends msg {msg} to learners")
            self.send_msg(self.network['learners']['ip'], self.network['learners']['port'], msg_encoded)

    def receive_msg(self, msg):
        print_stuff(f"{self} receives msg {msg}")

        if msg.phase == "REQUEST":
            # if self.leader:
            #     print_stuff("I am the leader.")
            self.create_state(self.num_instance)
            self.states[self.num_instance]['v'] = msg.data['v']
            if self.leader:
                self.phase_1A(self.num_instance)
            self.num_instance += 1
        elif msg.phase == "PHASE_1B":
            if self.leader:
                self.phase_2A(msg.instance, msg.data)
        elif msg.phase == "PHASE_2B":
            if self.leader:
                self.decide(msg.instance, msg.data)


class Acceptor(Agent):

    ''' Class representing acceptor agent '''

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, role="acceptors", *args, **kwargs)
        self.states = {}

    def create_state(self, instance):
        if instance not in self.states:
            self.states[instance] = {"rnd": 0, "v_rnd": 0, "v_val": None}

    def phase_1B(self, instance, data):
        if data['c_rnd'] >= self.states[instance]['rnd']:
            self.states[instance]['rnd'] = data['c_rnd']

        msg = Msg(instance)
        msg.fill_PHASE_1B(self.states[instance]['rnd'], self.states[instance]['v_rnd'], self.states[instance]['v_val'])
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends msg {msg} to proposers")
        self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)

    def phase_2B(self, instance, data):
        if data['c_rnd'] >= self.states[instance]['rnd']:
            self.states[instance]['v_rnd'] = data['c_rnd']
            self.states[instance]['v_val'] = data['c_val']

        msg = Msg(instance)
        msg.fill_PHASE_2B(self.states[instance]['v_rnd'], self.states[instance]['v_val'])
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends msg {msg} to proposers")
        self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)

    def receive_msg(self, msg):
        print_stuff(f"{self} receives msg {msg}")

        self.create_state(msg.instance)
        print_stuff(self.states[msg.instance])

        if msg.phase == "PHASE_1A":
            self.phase_1B(msg.instance, msg.data)
        elif msg.phase == "PHASE_2A":
            self.phase_2B(msg.instance, msg.data)


class Learner(Agent):

    ''' Class representing learner agent '''

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, role="learners", *args, **kwargs)
        self.states = {}

    def create_state(self, instance):
        if instance not in self.states:
            self.states[instance] = {'v': None}

    def receive_msg(self, msg):
        print_stuff(f"{self} receives msg {msg}")

        self.create_state(msg.instance)
        self.states[msg.instance]['v'] = msg.data['v_val']

        # for instance in range(0, len(self.states)):
        #     print(self.states[instance])

        print_stuff(f"Instance {msg.instance}:")
        print(self.states[msg.instance]['v'])
        print_stuff('\n')
