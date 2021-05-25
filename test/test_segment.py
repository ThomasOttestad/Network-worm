#!/usr/bin/env python3

import argparse
import logging
import os
import re
import subprocess
import tempfile
import time
import unittest
import json
import requests


def create_http_URL(address, header=""):
    return f"http://{address}/{header}"


def setup_worm():
    with open("../worm_segment/segment.bin", "rb") as file:
        data = file.read()

    wormgate_URL = create_http_URL(f"{args.host}:{args.port}")
    response = requests.post(
        wormgate_URL + f"worm_entrance?args={1}/{1}/{args.port}", data=data
    )
    time.sleep(1)


def kill_worm():
    leader_URL = create_http_URL(f"{args.host}:{args.port + 1}")
    print(f"kill{leader_URL}")
    response = requests.post(f"{leader_URL}kill")
    print(response)


def test_grow_worm():
    full_result = []

    wormgate_URL = create_http_URL(f"{args.host}:{args.port}")
    leader_URL = create_http_URL(f"{args.host}:{args.port + 1}")

    for i in range(1):
        for max_segments in range(1, args.size + 1):
            result = {}
            response = requests.post(f"{leader_URL}set_max_segments/{1}")

            start_time = time.time()
            response = requests.post(f"{leader_URL}set_max_segments/{max_segments}")
            end_time = time.time() - start_time

            print(f"grow from 1 to {max_segments} grow_time : {end_time}")
            response = requests.post(f"{leader_URL}set_max_segments/{1}")

            result["max"] = max_segments
            result["time"] = end_time
            full_result.append(result)

    response = requests.post(f"{leader_URL}set_max_segments/{1}")
    with open("result/grow.json", "w+") as file:
        json.dump(full_result, file)


def test_kill_worm():
    full_result = []

    wormgate_URL = create_http_URL(f"{args.host}:{args.port}", "info")
    leader_URL = create_http_URL(f"{args.host}:{args.port + 1}")
    response = requests.post(f"{leader_URL}set_max_segments/{args.size}")

    gate_info = requests.get(wormgate_URL, timeout=1).json()

    for i in range(3):
        for kill_size in range(2, 11):
            result = {}
            time.sleep(1)
            leader = requests.get(f"{leader_URL}segment_info", timeout=1).json()
            start_time = time.time()
            for i in range(1, kill_size):
                gate_URL = create_http_URL(gate_info["other_gates"][i], "kill_worms")
                response = requests.post(gate_URL)
            for gate in gate_info["other_gates"]:
                numseg = 0
                while numseg != 1:
                    gate_url = create_http_URL(gate, "info")
                    res = requests.get(gate_url, timeout=1).json()
                    numseg = res["numsegments"]
            end_time = time.time() - start_time
            print(f"kille_size: {kill_size - 1} kill_time : {end_time}")
            result["kill_size"] = kill_size - 1
            result["time"] = end_time
            full_result.append(result)

    response = requests.post(f"{leader_URL}set_max_segments/{1}")
    with open("result/kill.json", "w+") as file:
        json.dump(full_result, file)


def build_arg_parser():
    parser = argparse.ArgumentParser(prog="test_segment.py")

    parser.add_argument("-t", "--test", type=int)
    parser.add_argument("-c", "--host", type=str)
    parser.add_argument("-p", "--port", type=int)
    parser.add_argument("-n", "--size", type=int)

    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    global args
    args = parser.parse_args()
    print(args)

    setup_worm()
    if args.test == 1:
        test_grow_worm()
    elif args.test == 2:
        test_kill_worm()

    kill_worm()
