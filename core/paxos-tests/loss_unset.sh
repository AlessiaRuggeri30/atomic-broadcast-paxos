#!/usr/bin/env bash

IP=239.0.0.1

sudo iptables -S | grep $IP | sed 's/^-A //' | while read rule; do
    sudo iptables -D $rule
done

# for rule in `sudo iptables -S | grep $IP | sed 's/^-A //'`; do
#     echo $rule
# done
