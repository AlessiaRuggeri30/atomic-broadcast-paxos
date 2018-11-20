# Agent and roles

class Agent:

    ''' Generic class for paxos roles '''

    def __init__(self, agent_id, role):
        self.agent_id = agent_id
        self.role = role
        self.alive = True
        self.msgbox = Msgbox()
        self.counter = 0        # id of next sent message

    def run(self):

        ''' Wait for messages to handle '''

        pass

    def send_msg(self, m, receiver):
        msg = Msg(self.counter, m, self.agent_id, receiver)
        self.counter += 1

        # TODO IP multicast to receiver group

        return msg

    def receive_msg(self, msg):
        self.msgbox.push(msg)

    def stop(self):
        self.alive = False


class Proposer(Agent):

    ''' Class representing proposer agent '''

    def __init__(self, agent_id):
        Agent.__init__(self, agent_id, role="proposer")


class Acceptor(Agent):
    ''' Class representing acceptor agent '''

    def __init__(self, agent_id):
        Agent.__init__(self, agent_id, role="acceptor")


class Learner(Agent):
    ''' Class representing learner agent '''

    def __init__(self, agent_id):
        Agent.__init__(self, agent_id, role="learner")


# Handling messages

class Msg:

    ''' Class representing a message '''

    def __init__(self, msg_id, m, sender, receiver):
        self.msg_id = msg_id
        self.m = m
        self.sender = sender
        self.receiver = receiver

    def write(self, m):
        self.m = m

    def read(self):
        return str(self.m)

    def get_id(self):
        return str(self.msg_id)

    def get_sender(self):
        return str(self.sender)

    def get_receiver(self):
        return str(self.receiver)


class Msgbox:

    ''' Class representing the list of message that an agent received '''

    def __init__(self):
        self.queue = []

    def push(self, msg):
        self.queue.append(msg)

    def pop(self):
        return self.queue[0]

    def find_msg(self, msg_id, sender):
        for msg in self.queue:
            if msg.msg_id == msg_id and msg.sender == sender:
                return msg
        print("No requested message found")
        return None






















