#!/usr/bin/env bash

TEST="Test 3 - Learners learned every value that was sent by some client"

PROP=`cat prop.sorted | sort -u | wc -l`

for learned in $@; do
    LEARNED=`cat $learned | sort -u | wc -l`
    if [[ $LEARNED != $PROP ]]; then
	    echo "$TEST"
        echo "  > Failed!"
        exit 1
    fi
done

echo "$TEST"
echo "  > OK"

