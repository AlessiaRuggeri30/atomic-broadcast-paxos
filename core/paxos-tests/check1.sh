#!/usr/bin/env bash

TEST="Test 1 - Learners learned the same set of values in total order"

diff $1 $2 > test1.out

if [[ -s test1.out ]]; then
	echo "$TEST"
    echo "  > Failed!"
else
	echo "$TEST"
    echo "  > OK"
	rm test1.out
fi
