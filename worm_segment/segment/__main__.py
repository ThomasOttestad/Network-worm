#!/usr/bin/env python3
import requests
import time
import json
from os import sys
import socket
import http.server
import socketserver
import threading
import random
import urllib3
from urllib3.exceptions import NewConnectionError


def create_neighbour(address, id):
    return {"address": address, "id": int(id)}


def extract_id(address):
    return int(address[-5:]) - gate_port


def create_http_URL(address, header=""):
    return f"http://{address}/{header}"


def create_thread(function):
    function_thread = threading.Thread(target=function)
    function_thread.daemon = True
    function_thread.start()

    return function_thread


def log_error(error_msg, file_name):
    """Used for bugfixing"""
    with open(
        f"/home/giv008/INF-3203/worm-assignment-2021/log/{segment.addr}-{file_name}",
        "a+",
    ) as file:
        file.write(str(error_msg) + "\n")


class HttpRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log_message(format, *args, **kwargs):
        pass

    def send_whole_response(self, code, content, content_type=None):
        if isinstance(content, str):
            content = content.encode("utf-8")
            if not content_type:
                content_type = "text/plain"
            if content_type.startswith("text/"):
                content_type += "; charset=utf-8"

        elif isinstance(content, object):
            content = json.dumps(content, indent=2)
            content += "\n"
            content = content.encode("utf-8")
            content_type = "application/json"

        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.send_header("Content-length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        parsed_path = self.path.split("/")
        content_length = int(self.headers.get("content-length", 0))
        content = self.rfile.read(content_length)

        code = 400
        response = "Unknown path: " + self.path

        if parsed_path[1] == "kill":
            segment.shutdown()
            code = 200
            response = "KILL"
        elif parsed_path[1] == "set_max_segments":
            if segment.leader == True:
                if len(segment.gates) < int(parsed_path[2]):
                    code = 400
                    response = "Not enough gates for this wormsize!"
                else:
                    segment.set_max_segments(int(parsed_path[2]))
                    while segment.max_segments != len(segment.neighbours) + 1:
                        pass
                    code = 200
                    response = f"SET MAX SEGMENTS TO {parsed_path[2]}"
            else:
                code = 400
                response = (
                    f"{segment.addr} is not the leader, and cannot perform the request"
                )
        try:
            self.send_whole_response(code, response)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:
            log_error(e, "do_POST")

    def do_GET(self):
        parsed_path = self.path.split("/")

        response = "Unknown path: " + self.path
        if self.path == "/segment_info":
            code = 200
            response = segment.get_info()
        elif parsed_path[1] == "confirm_spawned":
            code = 200
            response = segment.post_spawned(parsed_path[2])

        try:
            self.send_whole_response(code, response)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:
            log_error(e, "do_GET")


class ThreadingHttpServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    def __init__(self, id, addr, gate, max_segments, leader, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id
        self.next_id = id + 1
        self.addr = addr
        self.max_segments = max_segments

        self.numsegments = 0
        self.neighbours = []
        self.not_confirmed_segments = []

        gate_addr = gate + f":{gate_port}"  # ":50000"
        self.gates = set()
        self.gates.update([gate_addr])

        if self.id == 1:
            self.leader = True
        else:
            self.leader = False
            self.init_not_leader(leader)

        self.get_all_gates(gate_addr)

    def get_all_gates(self, gate_addr):
        gate_URL = create_http_URL(gate_addr)
        res = self.worm_get_info(gate_URL)
        gate_list = list(self.gates)
        for gate in gate_list:
            URL = create_http_URL(gate)
            res = self.worm_get_info(URL)

    def get_num_segments(self):
        return len(self.not_confirmed_segments) + len(self.neighbours) + 1

    def get_info(self):
        return {
            "segment_addr": self.addr,
            "id": self.id,
            "neighbours": self.neighbours,
            "leader": self.leader,
            "max_segments": self.max_segments,
            "num_segments": len(self.neighbours) + 1,
            "next_id": self.next_id,
        }

    def post_spawned(self, addr):
        """Addr sent request confirming that he has spawned"""
        id = extract_id(addr)
        neighbour = create_neighbour(addr, id)
        self.neighbours.append(neighbour)
        try:
            self.not_confirmed_segments.remove({"id": id, "address": addr})
        except ValueError:
            print("Segment not in self.not_confirmed_segments")
        except Exception as e:
            log_error(e, "post_spawned")

        return self.get_info()

    def set_max_segments(self, max_segments):
        if max_segments >= 1:
            self.max_segments = max_segments
        else:
            print("Cannot set max_segments to less than 1!")

    def remove_neighbour(self, neighbour):
        try:
            self.neighbours.remove(neighbour)
        except ValueError:
            print(f"Neighbour: {neighbour} already removed!")
        except Exception as e:
            log_error(e, "remove_neighbour")

    def add_neighbour(self, new_neighbour):
        """Add new_neighbour if alive"""
        if (
            new_neighbour["address"] != self.addr
            and new_neighbour not in self.neighbours
        ):
            URL = create_http_URL(new_neighbour["address"], "segment_info")
            try:
                res = requests.get(url=URL).json()
                self.neighbours.append(new_neighbour)
            except (requests.exceptions.RequestException, BrokenPipeError) as e:
                """new_neighbour is assumed dead"""
                pass
            except Exception as e:
                log_error(e, "add_neighbour")

    def elect_new_leader(self):
        if not any(int(neighbour["id"]) < self.id for neighbour in self.neighbours):
            self.leader = True
        else:
            self.leader = False

    def init_not_leader(self, address):
        """Confirm  segment have been spawned to the leader"""
        URL = create_http_URL(address, f"confirm_spawned/{self.addr}")
        try:
            res = requests.get(url=URL).json()
        except requests.exceptions.ConnectionError:
            self.shutdown()
            return
        except Exception as e:
            log_error(e, "init_not_leader")

        if res["leader"]:
            self.max_segments = res["max_segments"]

        self.neighbours = res["neighbours"]
        self.neighbours.append(create_neighbour(address, extract_id(address)))
        self.remove_neighbour({"address": self.addr, "id": self.id})

    def ping_segments(self):
        """Ping all segments colleting all neighbours that are alive"""
        time.sleep(0.1)

        neighbours = self.neighbours
        for neighbour in neighbours:
            try:
                URL = create_http_URL(neighbour["address"], "segment_info")
                res = requests.get(url=URL).json()

                if res["leader"]:
                    self.max_segments = res["max_segments"]
                    self.next_id = res["next_id"]

                for s in res["neighbours"]:
                    self.add_neighbour(s)
            except (requests.exceptions.RequestException, BrokenPipeError) as e:
                self.remove_neighbour(neighbour)
                if int(neighbour["id"]) < self.id:
                    self.elect_new_leader()
            except Exception as e:
                log_error(e, "ping_segments")

    def leader_work(self):
        """Control size of worm"""
        for gate in list(self.gates):
            if len(self.neighbours) + 1 < self.max_segments:
                URL = create_http_URL(gate)
                res = self.worm_get_info(URL)
                if res["numsegments"] == 0:
                    self.wormgate_post_spawn_segment(gate)
            elif len(self.neighbours) + 1 > self.max_segments:
                if self.kill_spawned() == 0:
                    self.segment_kill()

    def worm_get_info(self, URL):
        res = requests.get(url=URL + "info").json()

        try:
            self.gates.update(res["other_gates"])
        except NameError:
            print(f"Wormgate {res['servername']} does not have other_gates!")
        except Exception as e:
            log_error(e, "worm_get_info_1")

        try:
            self.gates.remove(f"{self.addr.split(':')[0]}:{gate_port}")
        except Exception as e:
            log_error(e, "worm_get_info_2")
        return res

    def find_new_id(self):
        new_id = self.next_id
        self.next_id += 1

        return new_id

    def kill_spawned(self):
        """Kill not confirmed segment, and remove from self.not_confirmed_segments"""
        if len(self.not_confirmed_segments) > 0:
            seg = self.not_confirmed_segments.pop()
        else:
            return 0

        addr = seg["address"]
        url = create_http_URL(addr, "kill")
        try:
            response = requests.post(url)
        except requests.exceptions.RequestException:
            """Segment already killed"""
            pass
        except Exception as e:
            log_error(e, "kill_spawn")

        return 1

    def segment_kill(self):
        """Kill random segment in self.neighbours"""
        if len(self.neighbours) > 0:
            last_neighbour = self.neighbours.pop(-1)
        else:
            return

        try:
            URL = create_http_URL(last_neighbour["address"], "kill")
            response = requests.post(URL)
        except (requests.exceptions.RequestException, BrokenPipeError) as e:
            print(f"Segment: {last_neighbour} already killed!")
        except Exception as e:
            log_error(e, "segment_kill")

    def wormgate_post_spawn_segment(self, gate_addr):
        """Spawn new segment on gate_addr"""
        gate_URL = create_http_URL(gate_addr)
        new_id = self.find_new_id()

        response = requests.post(
            gate_URL
            + f"worm_entrance?args={new_id}/{self.max_segments}/{gate_port}/{self.addr}",
            data=data,
        )

        new_addr = f"{gate_addr.split(':')[0]}:{gate_port + new_id}"
        self.not_confirmed_segments.append({"id": new_id, "address": new_addr})


def parse_args():
    args = sys.argv[1].split("/")
    segment_id = int(args[0])
    max_segments = int(args[1])
    port = int(args[2])

    leader = None
    if len(args) == 4:
        leader = args[3]

    return segment_id, max_segments, port, leader


def run_http_server():
    gate_name = socket.gethostbyaddr(socket.gethostname())[1][0]

    global data
    with open(sys.argv[0], "rb") as file:
        data = file.read()

    global gate_port
    segment_id, max_segments, gate_port, leader = parse_args()
    segment_port = gate_port + segment_id
    segment_addr = f"{gate_name}:{segment_port}"

    global segment
    segment = ThreadingHttpServer(
        segment_id,
        segment_addr,
        gate_name,
        max_segments,
        leader,
        (gate_name, segment_port),
        HttpRequestHandler,
    )

    def segment_main():
        """Thread for http request handler"""
        segment.serve_forever()

    def leader_segment():
        """Thread for the leader"""
        while True:
            if segment.leader == True:
                segment.leader_work()

    def ping_segments():
        """Thread for the all of the segments"""
        time.sleep(2)
        while True:
            segment.ping_segments()

    ping_segments_thread = create_thread(ping_segments)
    main_thread = create_thread(segment_main)
    leader_thread = create_thread(leader_segment)

    main_thread.join()
    if main_thread.is_alive():
        segment.shutdown()


if __name__ == "__main__":
    run_http_server()