#!/bin/bash

MAX_SEGMENTS=1
usage="Usage: $0 -c <host:port> -o <info|kill|set_max_segments> -n(if -o == bin) <max_segments>"
while getopts ":hc:o:n:" opt; do
	case "$opt" in
		h  ) echo $usage; exit 1;;
		\? ) echo "Invalid option: -$OPTARG"; echo $usage; exit 1;;
		:  ) echo "-$OPTARG requires an argument"; exit 1;;
		c  ) HOST=$OPTARG;;
		o  ) OPERATION=$OPTARG;;
        n  ) MAX_SEGMENTS=$OPTARG;;
	esac
done
shift $(($OPTIND - 1))


if [ $OPERATION = "info" ]
then
    curl -X GET http://$HOST/segment_info

elif [ $OPERATION = "kill" ]
then
    curl -X POST http://$HOST/kill
elif [ $OPERATION = "set_max_segments" ]
then
    curl -X POST http://$HOST/set_max_segments/$MAX_SEGMENTS
else 
    echo "Invalid option chosen"
fi
