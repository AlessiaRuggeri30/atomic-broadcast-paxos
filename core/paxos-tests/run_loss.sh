#!/usr/bin/env bash

# Change the loss percentage here
LOSS=0.1

projdir="$1"
conf=`pwd`/paxos.conf
n="$2"

if [[ x$projdir == "x" || x$n == "x" ]]; then
	echo "Usage: $0 <project dir> <number of values per proposer>"
    exit 1
fi

# following line kills processes that have the config file in its cmdline
KILLCMD="pkill -f $conf"

$KILLCMD

cd $projdir

../loss_set.sh $LOSS

../generate.sh $n > ../prop1
../generate.sh $n > ../prop2

echo "starting acceptors..."

./acceptor.sh 1 $conf &
./acceptor.sh 2 $conf &
./acceptor.sh 3 $conf &

sleep 1
echo "starting learners..."

./learner.sh 1 $conf > ../learn1 &
./learner.sh 2 $conf > ../learn2 &

sleep 1
echo "starting proposers..."

./proposer.sh 1 $conf &
./proposer.sh 2 $conf &

echo "waiting to start clients"
sleep 10
echo "starting clients..."

./client.sh 1 $conf < ../prop1 &
./client.sh 2 $conf < ../prop2 &

sleep 5

$KILLCMD
wait

../loss_unset.sh

cd ..
