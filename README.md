
# Atomic Broadcast using Paxos Consensus Protocol
## Distributed algorithms, course project - USI, 2018
*Alessia Ruggeri*

This project was implemented as a university project for the course of *Distributed Algorithm* at Università della Svizzera Italiana.

**Paxos** is one of the oldest, simplest, and most versatile algorithms in the field of distributed algorithms. It is a consensus algorithm that works in asynchronous systems and with crash-faulty processes and it solves the problem of agreeing on one value among a group of participants (processes).

In fault-tolerant distributed computing, an **Atomic Broadcast** or total order broadcast is a broadcast where all correct processes in a system of multiple processes receive the same set of messages in the same order; that is, the same sequence of messages. The broadcast is termed "atomic" because it either eventually completes correctly at all participants, or all participants abort without side effects.

Atomic broadcasts can rely on Paxos consensus algorithm for the ordering of the messages. This is exactly the approach used in this project.

## Project structure

All the code can be found in the `./core` folder. In the `./core/paxos-test` folder there are the tests provided by the teaching assistant in order to test the functioning of the implemented protocol.

```
 .
├── core
│   ├── paxos-tests 
│   │   ├── paxos     // executables
│   │   |   ├── acceptor.sh
│   │   |   ├── client.sh
│   │   |   ├── learner.sh
│   │   |   ├── proposer.sh
│   │   ├── ...       // test stuff
│   ├── config.txt
│   ├── classes.py
│   ├── utils.py
│   ├── paxos.py
├── project.pdf
└── README.md
```

The core implementation can be found at `./core/paxos.py`, where classes and functions from `./core/classes.py` and `./core/utils.py` are used.

## Running the code

To run the code, the **executables** in `./core/paxos-test/paxos` can be used to start one process at a time having a defined role and id. On the terminal, you can run:

```bash
  ./ROLE.sh ID CONFIG_FILE
```
where ROLE can be *acceptor*, *client*, *learner* or *proposer*, ID is an integer number to identify the process and CONFIG_FILE is the configuration file containing ip address and communication port for each process role. Here is an example to run an acceptor with id equal to 1:

```bash
  ./acceptor.sh 1 ../paxos.conf
```

Otherwise, you can run the **tests** to have complete executions of the protocols. The instructions to run the tests are in the `README` file inside the `./core/paxos-test` folder, but as an example I provide here a simple execution of the protocol with 3000 requests for each client (in the terminal, you have to move inside the `./core/paxos-test` folder):

```bash
  ./run.sh paxos 3000
```

Then, to check the results of any test, just run:

```bash
  ./check_all.sh
```

In any execution, to enable all the prints conaining useful information to see what is going on and to debug, you can open the `./core/utils.py` file and just set the global variable:

```python
PRINTING = True
```


## Implementation

The Paxos protocol has been implemented using some classes as abstractions of processes and messages (can be found in `./core/classes.py`):
- **Agent**: generic class representing paxos processes.
- **Client**: class representing client agent.
- **Proposer**: class representing proposer agent.
- **Acceptor**: class representing acceptor agent.
- **Learner**: class representing learner agent.
- **Msg**: class representing a message exchanged by processes.

Inside the class methods it is implemented all the logic of the protocol, which respects almost exactly the implementation of the Paxos algorithm showed in the slides that we saw in class.

In my implementation, every time a client sends a request with a value, the leader starts a new Paxos instance proponing that value. The value is decided and sent to learners only if there is a quorum of acceptors voting for it.

### Leader Election

The leader election is very simple: the alive process that has the higher id number is the leader.

The leader have a timeout after which every time it sends a message to all other proposers informing them that it is the leader and it is alive. Other proposers also have a timeout after which they check if the leader is alive. If they suspect the leader to be dead, they restart leader election by claiming themselves to be leader, until the process with the highes id remains the only one sending the message "I AM TE LEADER".

### Proposer catch up

When a new proposer both born or become leader, it performs catch up in order to be updated about the current number of paxos intance and about the past decisions made.

To do catch up, the proposer asks the ```num_instance``` to acceptors and check if he has saved all the decided values up to that. If there are some missing values, for each one of them the proposer sends a "client request" specifying the number of the instance needed, so that Paxos for that instance is repeated.

In the decision phase, the leader sends the decided value both to the learners and the proposers, so that also the proposers can be always updated.

### Learner catch up

When a new learner born, it performs catch up in order to be updated about the current number of paxos intance and about the past decisions made.

To do catch up, the learner asks the ```num_instance``` to acceptors and check if he has saved all the decided values up to that. If there are some missing values, the learner asks to the leader the dictionary containing all decided values and it uses that to update its own dictionary.

### Delivery

The values are delivered by the learners in instance id order, so that all the learners deliver values in the same order. In this project, the delivery consists in printing the value.

A learner can deliver value with instance ```k+1``` only if it has already delivered values of instances from ```0``` to ```k```. This means that if there is some values that are missing between ```0``` and ```k``` in the learner's dictionary, the value ```k+1``` have to wait for the leader to do catch up before being delivered.
