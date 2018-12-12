#!/usr/bin/env bash

LOSS=$1

if [[ x$LOSS == "x" ]]; then
	echo "Usage: $0 <loss percentage (0.0 to 1.0)>"
    exit 1
fi


sudo iptables -A INPUT -d 239.0.0.1\
    -m statistic --mode random --probability $LOSS -j DROP
