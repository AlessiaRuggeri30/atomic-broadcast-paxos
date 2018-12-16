from threading import Thread
import time
import socket
import struct
import sys
import pickle
import math
from utils import print_stuff


# ----------------------------------------------------------------------------------------------------
#
# HANDLING MESSAGES
#
# ----------------------------------------------------------------------------------------------------


class Msg():

    """ Class representing a message exchanged by processes.
        It contains a method for each phase of the paxos algorithm
        and for some additional phases. Each method fills the message
        with the information related to that specific phase.
    """

    def __init__(self, instance=None, phase=None, data=None):
        """
            :param instance: int, optional
                The paxos instance to which the message is related.
            :param phase: str, optional
                The phase to which the message is related.
            :param data: dict, optional
                The information that this message is carrying.
        """
        self.instance = instance
        self.phase = phase
        self.data = data

    def encode(self):
        return pickle.dumps(vars(self))

    def decode(self, encoded):
        decoded = pickle.loads(encoded)
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

    def fill_DECISION(self, c_rnd, v_val):
        self.phase = "DECISION"
        self.data = {"c_rnd": c_rnd, "v_val": v_val}

    def fill_leader_sender(self, p_id):
        self.phase = "leader_sender"
        self.data = {"p_id": p_id}

    def fill_catch_up_instance(self, num_instance=None, role=None):
        self.phase = "catch_up_instance"
        self.data = {"num_instance": num_instance, "role": role}

    def fill_catch_up_learners(self, decisions=None):
        self.phase = "catch_up_learners"
        self.data = decisions

    def update_c_rnd(self, c_rnd):
        self.phase = "update_c_rnd"
        self.data = {"c_rnd": c_rnd}


# ----------------------------------------------------------------------------------------------------
#
# AGENTS AND ROLES
#
# ----------------------------------------------------------------------------------------------------


class Agent(Thread):

    """ Generic class representing paxos processes. It inherits from Thread. """

    def __init__(self, role, ip, port, p_id, network):
        """
            :param role: str
                The paxos role of the process.
            :param ip: str
                The ip of the process.
            :param port: int
                The communication port of the process.
            :param p_id: int
                The process id.
            :param network: dict
                The network containing processes info.
        """
        Thread.__init__(self)
        self.role = role
        self.ip = ip
        self.port = port
        self.p_id = p_id
        self.server = self.setup_server()   # socket for the server side
        self.client = self.setup_client()   # socket for the client side
        self.network = network

    def __str__(self):
        return str((self.role, self.ip, self.port, self.p_id))

    def __repr__(self):
        return self.__str__()

    def update_state(self, instance):
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
            encoded_msg, address = self.server.recvfrom(2**16)
            msg = Msg()
            msg.decode(encoded_msg)
            self.receive_msg(msg)       # behave in a specific way based on the process role

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
            # v = input()
            # self.request(v)
            for value in sys.stdin:
                value = value.strip()
                self.request(value)
                time.sleep(0.001)

    def request(self, v):
        """ Send a request to proposers.

                :param v: int or str
                    Value to be proposed
        """
        msg = Msg()
        msg.fill_REQUEST(v)
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends request msg {msg} to proposers")
        self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)


class Proposer(Agent):

    """ Class representing proposer agent. """

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, role="proposers", *args, **kwargs)
        self.states = {}                # for each paxos instance, it saves the related values
        self.leader = True              # the proposer is or is not the leader
        self.num_instance = -1          # greater instance identifying number seen
        self.instance_updated = False   # the proposer is or is not up to date with num_instance
        self.catch_up_counter = 0       # counter for quorum in the catch up phase
        self.max_num_acceptors = 3      # needed to compute quorum

        self.leader_sender = Thread(target=self.leader_sender)      # sends message if proposer is the leader
        self.leader_listener = Thread(target=self.leader_listener)  # listen to the leader messages
        self.leader_sender.daemon = True
        self.leader_listener.daemon = True
        self.leader_sender_interval = 1         # interval of seconds between leader_sender messages
        self.leader_listener_interval = 2       # interval of seconds for leader_listener control
        self.last_msg_leader_time = None        # time of the last message received from the leader

    def catch_up_instance(self):
        """ Sends a message to acceptors to know the updated num_instance. """
        msg = Msg()
        msg.fill_catch_up_instance(role="proposers")
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends catch up request to acceptors")
        self.send_msg(self.network['acceptors']['ip'], self.network['acceptors']['port'], msg_encoded)

    def catch_up_request(self, instance):
        """ Sends a "client" request with specific instance to know the decision made in that instance.

            :param instance: int
                Number of the instance of which the proposer whant to know the decision made.
         """
        msg = Msg(instance)
        msg.fill_REQUEST(None)
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends catch up request to proposers")
        self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)

    def catch_up_control(self):
        """ Check if the proposer is updated with all the instances in memory.
            If not, it asks for the missing instances.
        """
        for i in range(0, self.num_instance + 1):
            if i != -1 and i not in self.states:
                self.catch_up_request(i)

    def handle_catch_up(self, msg):
        """ Handles the receiving of a num_instance update sent by acceptors.

            :param msg: class
                Message received by acceptors
        """
        if self.instance_updated:       # proposer had already updated num_instance when it was born
            if msg.data['num_instance'] > self.num_instance:
                self.num_instance = msg.data['num_instance']
        else:                           # first time updating num_instance
            self.catch_up_counter += 1
            if msg.data['num_instance'] > self.num_instance:
                self.num_instance = msg.data['num_instance']
            if self.catch_up_counter == math.ceil((self.max_num_acceptors + 1) / 2):
                self.catch_up_counter = 0
                self.instance_updated = True
                print_stuff("Instance updated")
        self.catch_up_control()         # after having updated num_instance, check to have all instances in memory

    def catch_up_learners(self):
        """ Handles the receiving of a request of update sent by learners.
            The leader sends back to the learners a dictionary containing
            all the values decided until now.
        """
        decisions = {}
        for instance in self.states:
            if self.states[instance]['c_val'] is not None:
                decisions[int(instance)] = int(self.states[instance]['c_val'])
            else:
                decisions[int(instance)] = None
        if len(decisions) == 0:
            decisions = None
        msg = Msg()
        msg.fill_catch_up_learners(decisions)
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends catch up learners to learners")
        self.send_msg(self.network['learners']['ip'], self.network['learners']['port'], msg_encoded)

    def run(self):
        if not self.leader_sender.is_alive():
            self.leader_sender.start()
        if not self.leader_listener.is_alive():
            self.leader_listener.start()
        self.server.bind((self.ip, self.port))
        print_stuff(f"{self} is listening")
        self.catch_up_instance()
        while True:
            encoded_msg, address = self.server.recvfrom(2**16)
            msg = Msg()
            msg.decode(encoded_msg)
            self.receive_msg(msg)

    def leader_sender(self):
        """ Sends message if proposer is the leader. """
        while True:
            time.sleep(self.leader_sender_interval)
            if self.leader:
                msg = Msg()
                msg.fill_leader_sender(self.p_id)
                msg_encoded = msg.encode()
                print_stuff(f"{self} sends msg: I AM THE LEADER")
                # print(self.states)
                self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)

    def leader_listener(self):
        """ Listen to the leader messages and check if it may be dead. """
        while True:
            time.sleep(0.001)
            if self.last_msg_leader_time is not None:
                current_time = time.time()
                interval = current_time - self.last_msg_leader_time
                if not self.leader:
                    if interval > self.leader_listener_interval:
                        print_stuff("Probably leader is dead")
                        self.leader = True
                        self.catch_up_instance()

    def update_state(self, instance):
        """ Add instance to the dictionary.
                :param instance: int
                    Instance to be added
        """
        if instance is not None and instance not in self.states:
            self.states[int(instance)] = {"c_rnd": self.p_id + 1, "c_val": None, "v": None,
                                     "max_v_rnd": 0, "max_v_val": 0,
                                     "quorum1B": 0, "quorum2B": 0}

    def phase_1A(self, instance):
        """ Handle phase 1A of Paxos algorithm. """
        # print("Phase 1A")
        msg = Msg(instance)
        msg.fill_PHASE_1A(self.states[instance]['c_rnd'])
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends msg {msg} to acceptors")
        self.send_msg(self.network['acceptors']['ip'], self.network['acceptors']['port'], msg_encoded)

    def phase_2A(self, instance, data):
        """ Handle phase 2A of Paxos algorithm. """
        # print("Phase 2A")
        if data['rnd'] == self.states[instance]['c_rnd']:
            self.states[instance]['quorum1B'] += 1
        print_stuff(self.states[instance]['max_v_rnd'])
        if data['v_rnd'] >= self.states[instance]['max_v_rnd']:
            self.states[instance]['max_v_rnd'] = data['v_rnd']
            self.states[instance]['max_v_val'] = data['v_val']
        if self.states[instance]['quorum1B'] >= math.ceil((self.max_num_acceptors+1) / 2):  # if it has quorum
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
        """ Handle phase decide of Paxos algorithm. """
        # print("Deciding")
        if data['v_rnd'] == self.states[instance]['c_rnd']:
            self.states[instance]['quorum2B'] += 1
        if self.states[instance]['quorum2B'] >= math.ceil((self.max_num_acceptors+1) / 2):  # if it has quorum
            self.states[instance]['quorum2B'] = 0  # reset quorum

            msg = Msg(instance)
            msg.fill_DECISION(self.states[instance]['c_rnd'], self.states[instance]['c_val'])
            msg_encoded = msg.encode()
            print_stuff(f"{self} sends msg {msg} to learners")
            self.send_msg(self.network['learners']['ip'], self.network['learners']['port'], msg_encoded)
            self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)

    def receive_msg(self, msg):
        """ Handle the receiving of a new message. """
        print_stuff(f"{self} receives msg {msg}")

        self.update_state(msg.instance)

        if msg.phase == "REQUEST":
            if msg.instance is None:        # request for a new instance
                self.num_instance += 1
                self.update_state(self.num_instance)
                num_instance = self.num_instance
            else:                           # request for the value decided in an old instance
                num_instance = int(msg.instance)
            self.states[num_instance]['v'] = msg.data['v']
            if not self.instance_updated:
                self.catch_up_instance()
            # assuming that the max number of proposers is 1000
            self.states[num_instance]['c_rnd'] = self.states[num_instance]['c_rnd'] + 1000
            if self.leader and self.instance_updated:
                self.phase_1A(num_instance)
        elif msg.phase == "PHASE_1B":
            if self.leader:
                self.phase_2A(int(msg.instance), msg.data)
        elif msg.phase == "PHASE_2B":
            if self.leader:
                self.decide(int(msg.instance), msg.data)
        elif msg.phase == "DECISION":
            # print(f"Proposer {self.p_id} update {msg}")
            self.update_state(msg.instance)
            self.states[int(msg.instance)]['c_rnd'] = msg.data['c_rnd']
            self.states[int(msg.instance)]['c_val'] = msg.data['v_val']
        elif msg.phase == "leader_sender":
            self.last_msg_leader_time = time.time()
            if msg.data['p_id'] > self.p_id:
                self.leader = False
        elif msg.phase == "catch_up_instance":
            self.handle_catch_up(msg)
        elif msg.phase == "catch_up_learners":
            if self.leader:
                self.catch_up_learners()


class Acceptor(Agent):

    """ Class representing acceptor agent. """

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, role="acceptors", *args, **kwargs)
        self.states = {}            # for each paxos instance, it saves the related values
        self.num_instance = -1      # greater instance identifying number seen

    def update_state(self, instance):
        """ Add instance to the dictionary.
                :param instance: int
                    Instance to be added
        """
        if instance is not None and instance not in self.states:
            self.states[instance] = {"rnd": 0, "v_rnd": 0, "v_val": None}

    def phase_1B(self, instance, data):
        """ Handle phase 1B of Paxos algorithm. """
        # print("Phase 1B")
        if data['c_rnd'] >= self.states[instance]['rnd']:
            self.states[instance]['rnd'] = data['c_rnd']

            msg = Msg(instance)
            msg.fill_PHASE_1B(self.states[instance]['rnd'], self.states[instance]['v_rnd'], self.states[instance]['v_val'])
            msg_encoded = msg.encode()
            print_stuff(f"{self} sends msg {msg} to proposers")
            self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)

    def phase_2B(self, instance, data):
        """ Handle phase 2B of Paxos algorithm. """
        # print("Phase 2B")
        if data['c_rnd'] >= self.states[instance]['rnd']:
            self.states[instance]['v_rnd'] = data['c_rnd']
            self.states[instance]['v_val'] = data['c_val']

            msg = Msg(instance)
            msg.fill_PHASE_2B(self.states[instance]['v_rnd'], self.states[instance]['v_val'])
            msg_encoded = msg.encode()
            print_stuff(f"{self} sends msg {msg} to proposers")
            self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)

    def handle_catch_up(self, role):
        """ Handles the receiving of the request of a num_instance update.

            :param role: str
                The role of the process that sent the update request.
        """
        msg = Msg()
        msg.fill_catch_up_instance(num_instance=self.num_instance)
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends msg {msg} to {role}")
        self.send_msg(self.network[role]['ip'], self.network[role]['port'], msg_encoded)

    def receive_msg(self, msg):
        """ Handle the receiving of a new message. """
        print_stuff(f"{self} receives msg {msg}")

        self.update_state(msg.instance)
        if msg.instance is not None and int(msg.instance) > self.num_instance:
            self.num_instance = int(msg.instance)

        if msg.phase == "PHASE_1A":
            self.phase_1B(int(msg.instance), msg.data)
        elif msg.phase == "PHASE_2A":
            self.phase_2B(int(msg.instance), msg.data)
        elif msg.phase == "catch_up_instance":
            self.handle_catch_up(msg.data['role'])


class Learner(Agent):

    """ Class representing learner agent. """

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, role="learners", *args, **kwargs)
        self.states = {}
        self.can_deliver = True
        self.last_delivered = -1
        self.num_instance = -1

    def catch_up_instance(self):
        """ Sends a message to acceptors to know the updated num_instance. """
        msg = Msg()
        msg.fill_catch_up_instance(role="learners")
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends catch up request to acceptors")
        self.send_msg(self.network['acceptors']['ip'], self.network['acceptors']['port'], msg_encoded)

    def catch_up_learners(self):
        """ Sends a message to proposers to know the updated decided values. """
        msg = Msg()
        msg.fill_catch_up_learners()
        msg_encoded = msg.encode()
        print_stuff(f"{self} sends catch up learners to proposers")
        self.send_msg(self.network['proposers']['ip'], self.network['proposers']['port'], msg_encoded)

    def catch_up_control(self):
        """ Check if the learner is updated with all the instances in memory.
            If not, it asks for the missing instances.
        """
        for i in range(0, self.num_instance + 1):
            if i != -1 and i not in self.states:
                self.can_deliver = False
                break
        print_stuff(f" {self} Can deliver? {self.can_deliver}")
        if not self.can_deliver:
            self.catch_up_learners()
        else:
            self.deliver()

    def handle_catch_up(self, msg):
        """ Handles the receiving of a num_instance update sent by acceptors.

            :param msg: class
                Message received by acceptors
        """
        if msg.data['num_instance'] > self.num_instance:
            if self.num_instance == -1:     # learner is just born and have to update also decide values
                self.num_instance = msg.data['num_instance']
                self.catch_up_control()
            else:
                self.num_instance = msg.data['num_instance']

    def update_decisions(self, decisions):
        """ Handles the receiving of a decisions update sent by the leader proposer.
            It update the learner dictionary with the missing decisions.

            :param decisions: dict
                Dictionary of decisions sent by leader
        """
        if decisions is not None:
            if len(decisions) - 1 > self.num_instance:
                self.num_instance = len(decisions) - 1
            for instance in decisions:
                if int(instance) not in self.states or self.states[int(instance)]['v'] is None:
                    self.states[int(instance)] = {'v': decisions[instance]}
        self.can_deliver = True
        self.catch_up_control()

    def run(self):
        self.server.bind((self.ip, self.port))
        print_stuff(f"{self} is listening")
        self.catch_up_instance()
        while True:
            encoded_msg, address = self.server.recvfrom(2**16)
            msg = Msg()
            msg.decode(encoded_msg)
            self.receive_msg(msg)

    def update_state(self, instance):
        """ Add instance to the dictionary.
                :param instance: int
                    Instance to be added
        """
        if instance not in self.states:
            self.states[instance] = {'v': None}

    def deliver(self):
        """ Deliver all values from the last delivered to the maximum instance value. """
        for i in range((self.last_delivered + 1), (len(self.states))):
            if i in self.states and self.states[i]['v'] is not None:
                print_stuff(f"Instance {i}:")
                print(self.states[i]['v'], flush=True)          # deliver
        self.last_delivered = len(self.states)-1

    def receive_msg(self, msg):
        """ Handle the receiving of a new message. """
        print_stuff(f"{self} receives msg {msg}")

        if msg.phase == "DECISION":
            if msg.instance is not None and int(msg.instance) > self.num_instance:
                self.num_instance = int(msg.instance)
            self.update_state(msg.instance)
            self.states[int(msg.instance)]['v'] = msg.data['v_val']
            self.can_deliver = True
            self.catch_up_control()
        elif msg.phase == "catch_up_instance":
            self.handle_catch_up(msg)
        elif msg.phase == "catch_up_learners":
            self.update_decisions(msg.data)

