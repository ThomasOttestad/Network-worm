# Spawn N segments on host C port P 
    ./wormgate_http.sh -o bin -c C -p P -n N

# Kill all segments on all gates
    ./wormgate_http.sh -o kill_all

# Get Info from host C port P
    ./wormgate_http.sh -o info -c C

# Kill all segments on host C port P
    ./wormgate_http.sh -o kill -c C

# Segment leader address:
    The first leader will be on the same computer wormgate as where the first segment was spawned.
    It will have portnumber of the host + 1
    Example:
    	wormgate: compute-1-1:50000
    	leader  : compute-1-1:50001

# Get info from segment C(host:port)
    ./segment_http.sh -o info -c C

# Kill segment C(host:port)
    ./segment_http.sh -o kill -c C

# Set max segments (can only be sent to leader) to size N on host C(host:port)
    ./segment_http.sh -o set_max_size -c C


