import argparse
import socket
import threading
from random import randint
from collections import deque
import ServerClient

from packet import Packet
M = 3
SEQUENCE_NUM_LIMIT = 2**M # not used any more
WINDOW_SIZE = 2**(M-1)


msg = ["Hello World", "this is Mat", "sending some packets",
       "testing the SelRep", "hopefully this works", "let me know", "thanks",
       "test1", "test2", "test3", "test4", "test5", "test6", "test7", "test8",
       "test9", "test10", "test11", "test12", "test13", "test14", "test15", "test16",
       "test17", "test18", "test19", "test20", "test21", "test22", "test23", "test24",
       "test25", "test26", "test27", "test28", "test29", "test30", "test31", "test32",
       "test33", "test34", "test35", "test36", "test37", "test38", "test39", "test40",
       "test41", "test42", "test43", "test44", "test45", "test46", "test47", "test48"]


def run_server(port):
    # this function handles a new client and sends them for handshaking
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        conn.bind(('', port))
        print('Main server is listening at', port)
        while True:
            data, sender = conn.recvfrom(1024)
            threading.Thread(target=handshake_and_listen, args=(data, sender)).start()

    finally:
        conn.close()


def handshake_and_listen(data, sender):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = 60

    while True:
        try:
            # this thread gets ins own connection port
            port = randint(50000, 60000)
            conn.bind(('', port))

            # send handshake packet
            p = Packet.from_bytes(data)
            p.packet_type = 4
            p.payload = str(port).encode("utf-8")
            conn.sendto(p.to_bytes(), sender)

            print('Sending handshake packet, Server is listening for a client at', port)
            while True:
                conn.settimeout(timeout)
                data, sender = conn.recvfrom(1024)
                threading.Thread(target=handle_client, args=(conn, data, sender)).start()

        except socket.timeout:
            print('No response after {}s, timing out'.format(timeout))
            conn.close()
            break
        except OSError as e:
            print("OSError: ", e)
            conn.close()
            break
        except Exception as e:
            print("Error: ", e)
            conn.close()
            break


def handle_client(conn, data, sender):
    print ("new thread started")
    try:
        p = Packet.from_bytes(data)

        p.packet_type = 1
        print("Router: ", sender)
        print("Packet: ", p)
        print("Payload: ", p.payload.decode("utf-8"))

        # How to send a reply.
        # The peer address of the packet p is the address of the client already.
        # We will send the same payload of p. Thus we can re-use either `data` or `p`.
        conn.sendto(p.to_bytes(), sender)

    except Exception as e:
        print("Error: ", e)


def main():

    # Usage python udp_server.py [--port port-number]
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="echo server port", type=int, default=8007)
    args = parser.parse_args()
    run_server(args.port)


if __name__ == "__main__":
    main()
