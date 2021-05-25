#!/bin/bash
/share/apps/ifi/available-nodes.sh | grep compute | shuf | head -n $1 > hostfile

PORT=$2

> wormgates.txt

while read LINE; do
    echo "$LINE:$PORT" >> wormgates.txt
done  < hostfile
