#!/usr/bin/env bash

# Generate n random numbers

n="$1"

if [[ $n == "" ]]; then
	echo "Usage $0 <number of values>"
	exit
fi

for (( i = 0; i < $n; i++ )); do
	echo $RANDOM
done
