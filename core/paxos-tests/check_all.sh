#!/usr/bin/env bash

./check1.sh learn1 learn2
cat prop1 prop2 | sort > prop.sorted
./check2.sh learn1 learn2
./check3.sh learn1 learn2
