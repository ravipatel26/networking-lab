import argparse
import socket

from packet import Packet
M = 3
SEQUENCE_NUM_LIMIT = 2**M
WINDOW_SIZE = 2**(M-1)

window = [False] * WINDOW_SIZE

msg = ["Hello World", "this is Mat", "sending some packets",
       "testing the SelRep", "hopefully this works", "let me know", "thanks",
       "test1", "test2", "test3", "test4", "test5", "test6", "test7", "test8",
       "test9", "test10", "test11", "test12", "test13", "test14", "test15", "test16",
       "test17", "test18", "test19", "test20", "test21", "test22", "test23", "test24",
       "test25", "test26", "test27", "test28", "test29", "test30", "test31", "test32",
       "test33", "test34", "test35", "test36", "test37", "test38", "test39", "test40",
       "test41", "test42", "test43", "test44", "test45", "test46", "test47", "test48"]


def run_server(port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        conn.bind(('', port))
        print('Echo server is listening at', port)
        while True:
            data, sender = conn.recvfrom(1024)
            handle_client(conn, data, sender)

    finally:
        conn.close()


def handle_client(conn, data, sender):
    try:
        p = Packet.from_bytes(data)
        print("Router: ", sender)
        print("Packet: ", p)
        print("Payload: ", p.payload.decode("utf-8"))

        # How to send a reply.
        # The peer address of the packet p is the address of the client already.
        # We will send the same payload of p. Thus we can re-use either `data` or `p`.
        conn.sendto(p.to_bytes(), sender)

    except Exception as e:
        print("Error: ", e)


# Usage python udp_server.py [--port port-number]
parser = argparse.ArgumentParser()
parser.add_argument("--port", help="echo server port", type=int, default=8007)
args = parser.parse_args()
run_server(args.port)
