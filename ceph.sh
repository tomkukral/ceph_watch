#!/bin/bash
while true; do
	echo "--- mark ---"
	while read l; do
		echo "$l"
		sleep 0.3
	done < ./test_log
done
