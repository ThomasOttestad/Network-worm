#!/bin/bash

while read LINE
do
    curl -X POST http://$LINE/kill_worms 
done < ../worm_gate/wormgates.txt