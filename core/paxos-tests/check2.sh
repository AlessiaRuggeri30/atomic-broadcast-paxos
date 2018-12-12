#!/usr/bin/env bash

TEST="Test 2 - Values learned were actually proposed"

PROP_LEARNED=`cat prop.sorted $@ | sort -u | wc -l`
PROP=`cat prop.sorted | sort -u | wc -l`

if [[ $PROP_LEARNED == $PROP ]]; then
	echo "$TEST"
    echo "  > OK"
else
	echo "$TEST"
    echo "  > Failed!"
fi
