#!/bin/bash

MAX_SEGMENTS=1

usage="Usage: $0 -c <host> -p <port> -o <info|bin|kill> -n(if -o == bin) <max_segments>"
while getopts ":hc:o:n:e:p:" opt; do
	case "$opt" in
		h  ) echo $usage; exit 1;;
		\? ) echo "Invalid option: -$OPTARG"; echo $usage; exit 1;;
		:  ) echo "-$OPTARG requires an argument"; exit 1;;
		c  ) HOST=$OPTARG;;
        p  ) PORT=$OPTARG;;
		o  ) OPERATION=$OPTARG;;
        n  ) MAX_SEGMENTS=$OPTARG;;
        e  ) NOTHOST=$OPTARG;;
	esac
done

HOST="$HOST:$PORT"

shift $(($OPTIND - 1))
if [ $OPERATION = "info" ]
then
    curl -X GET http://$HOST/info

elif [ $OPERATION = "bin" ]
then
    ./make_python_zip_executable.sh segment
    curl -X POST http://$HOST/worm_entrance?args=1/$MAX_SEGMENTS/$PORT \
    --data-binary @segment.bin
elif [ $OPERATION = "kill" ]
then
    curl -X POST http://$HOST/kill_worms 
elif [ $OPERATION = "kill_all" ]
then
    while read LINE
    do
        curl -X POST http://$LINE/kill_worms &
    done < ../worm_gate/wormgates.txt
else 
    echo "Invalid option chosen"
fi