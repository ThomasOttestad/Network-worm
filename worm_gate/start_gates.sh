#!/bin/bash

usage="Usage: $0 -p <port> -n <num_gates>"
while getopts ":hp:n:" opt; do
	case "$opt" in
		h  ) echo $usage; exit 1;;
		\? ) echo "Invalid option: -$OPTARG"; echo $usage; exit 1;;
		:  ) echo "-$OPTARG requires an argument"; exit 1;;
		p  ) PORT=$OPTARG;;
		n  ) SIZE=$OPTARG;;
	esac
done
shift $(($OPTIND - 1))

./generate_wormgates.sh  $SIZE $PORT 


cwd="$PWD" 
while read LINEA
do
    NEIGHBOUR=''
    HOST=${LINEA: 0:-6}
    while read LINEB
    do 
        if [ "$LINEA" != "$LINEB" ]
        then
            NEIGHBOUR="$NEIGHBOUR $LINEB"
            PORT=${LINEA: -5}
        fi
    done < wormgates.txt
    (set -x; ssh -f "$HOST" "python3 $cwd/wormgate.py -p "$PORT" $NEIGHBOUR")
done < wormgates.txt