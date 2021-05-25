# NOTE!!
    Need to setup wormgates with 'other_gates' before running test
    Then use address of one wormgate for computer and port.

# Test GROW from 1 to N computer C with port P
    python3 test_segment.py -c C -p P -n N -t 1

# Test recover from killing 1 to 9 on computer C with port P wormsize N
    python3 test_segment.py -c C -p P -n N -t 2
