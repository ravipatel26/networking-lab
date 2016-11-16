import argparse
import ipaddress
import socket
import threading

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


def test():
    print("timer done")


def run_client(router_addr, router_port, server_addr, server_port):
    peer_ip = ipaddress.ip_address(socket.gethostbyname(server_addr))
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = 5
    try:
        timer1 = threading.Timer(5.0, test)
        timer1.start()
        timer1.cancel()
        timer1.join()
        timer1.run()
        timer1.start()
        print ("Hello, World!")
        window = [False, False, False, False, False]

        seq = 0
        last_pkt = len(msg)-1
        for x in range(0, WINDOW_SIZE):
            p = Packet(packet_type=0,
                       seq_num=seq,
                       peer_ip_addr=peer_ip,
                       peer_port=server_port,
                       payload=msg[x].encode("utf-8"))
            conn.sendto(p.to_bytes(), (router_addr, router_port))
            print('Send "{}" to router'.format(msg[x]))

            seq += 1
            if seq == SEQUENCE_NUM_LIMIT:
                seq = 0

        # Try to receive a response within timeout
        conn.settimeout(timeout)
        print('Waiting for a response')
        response, sender = conn.recvfrom(1024)
        p = Packet.from_bytes(response)
        print('Router: ', sender)
        print('Packet: ', p)
        print('Payload: ' + p.payload.decode("utf-8"))

    except socket.timeout:
        print('No response after {}s'.format(timeout))
    finally:
        conn.close()


# Usage:
# python echoclient.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007

parser = argparse.ArgumentParser()
parser.add_argument("-rh", help="router host", default="localhost")
parser.add_argument("-rp", help="router port", type=int, default=3000)

parser.add_argument("-sh", help="server host", default="localhost")
parser.add_argument("-sp", help="server port", type=int, default=8007)
args = parser.parse_args()

run_client(args.rh, args.rp, args.sh, args.sp)
