import argparse
import ipaddress
import socket
import threading
from collections import deque

from packet import Packet
M = 3
SEQUENCE_NUM_LIMIT = 2**M # not used anymore, never-ending sequence
WINDOW_SIZE = 2**(M-1)


msg = ["Hello World", "this is Mat", "sending some packets",
       "testing the SelRep", "hopefully this works", "let me know", "thanks",
       "test1", "test2", "test3", "test4", "test5", "test6", "test7", "test8",
       "test9", "test10", "test11", "test12", "test13", "test14", "test15", "test16",
       "test17", "test18", "test19", "test20", "test21", "test22", "test23", "test24",
       "test25", "test26", "test27", "test28", "test29", "test30", "test31", "test32",
       "test33", "test34", "test35", "test36", "test37", "test38", "test39", "test40",
       "test41", "test42", "test43", "test44", "test45", "test46", "test47", "test48"]
last_pkt = len(msg)-1

window_status = deque()
msg_buffer = deque()


def test():
    print("timer done")


def send_udp_pkt(router_addr, router_port, peer_ip, server_port, conn, seq, slide_window, lock):
    timeout = 3
    resend = True
    seq_num = str(seq)

    while resend:
        try:

            # check if seq in buffer (received by other thread)
            while True:
                have_lock = lock.acquire(0)
                try:
                    if have_lock:
                        for s in msg_buffer:
                            if s.seq_num == seq:
                                print("Found correct packet seq# " +seq_num+" in buffer")
                                rp = s
                                msg_buffer.remove(s)
                                resend = False
                finally:
                    if have_lock:
                        lock.release()
                        break

            if resend:
                print('Send packet '+seq_num+' and listen for '+str(timeout)+'s')
                # create the packet
                p = Packet(packet_type=0,
                           seq_num=seq,
                           peer_ip_addr=peer_ip,
                           peer_port=server_port,
                           payload=msg[seq].encode("utf-8"))

                # Send this packet out and start the timer for it
                conn.sendto(p.to_bytes(), (router_addr, router_port))

                #########################################################
                #    program will wait here until receive or timeout    #
                #########################################################
                conn.settimeout(timeout)
                response, sender = conn.recvfrom(1024)
                # If a packet is received, check matching seq #
                rp = Packet.from_bytes(response)
                if rp.seq_num == seq:
                    print("Received correct packet # "+seq_num)
                    resend = False
                else:
                    print("Was expecting "+seq_num+", but got " + str(rp.seq_num) +
                          ", buffering it, search buf before resend.")
                    while True:
                        have_lock = lock.acquire(0)
                        try:
                            if have_lock:
                                msg_buffer.append(rp)

                        finally:
                            if have_lock:
                                lock.release()
                                break

        except OverflowError:
            print('\nOverflow Error (seq # got too big?)\n')
            break
        except socket.timeout:
            print('No response for seq# "{}" after {}s'.format(seq_num, timeout))
            continue

    #########################################################
    #       This packet has now been acknowledged           #
    #########################################################
    # correct packet is received
    if not resend:
        '''print('Router: ', sender)
        print('Packet: ', rp)
        print('Payload: ' + rp.payload.decode("utf-8"))'''

        with slide_window:
            while seq != window_status[0]:
                print ("Thread w/seq# " + seq_num + " is waiting to finish.")
                print (window_status)
                slide_window.wait()

            print ("Thread w/seq# " + seq_num + " is done waiting, notify slide window")
            window_status.popleft()

            # if there's more packets to be sent, start a new thread to handle it
            if len(window_status) != 0 and window_status[len(window_status) - 1] + 1 <= last_pkt:
                next_seq = window_status[len(window_status) - 1] + 1
                window_status.append(next_seq)
                threading.Thread(target=send_udp_pkt,
                                 args=(router_addr, router_port, peer_ip, server_port, conn, next_seq, slide_window,
                                       lock)).start()

            while True:
                file_lock = lock.acquire(0)
                try:
                    if file_lock:
                        f = open("logfile.txt", 'a')
                        f.write(str(rp.payload) + "\n")
                        f.close()

                finally:
                    if file_lock:
                        lock.release()
                        break

            slide_window.notifyAll()

    print ("window: " + str(window_status))
    print ("buffer: " + str(msg_buffer))

    # clear potential duplicate msg_buffer entries
    while True:
        have_lock = lock.acquire(0)
        try:
            if have_lock:
                for s in msg_buffer:
                    if s.seq_num <= seq:
                        print("Removing old buffer entry seq# " + seq_num)
                        msg_buffer.remove(s)
        finally:
            if have_lock:
                lock.release()
                break

    if rp.seq_num == last_pkt:
        print ("final thread finishing")
        # output to file
        f = open("logfile.txt", 'a')
        f.write(str(window_status) + "\n" + str(msg_buffer))
        f.close()


def main():

    # Usage:
    # python echoclient.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007

    parser = argparse.ArgumentParser()
    parser.add_argument("-rh", help="router host", default="localhost")
    parser.add_argument("-rp", help="router port", type=int, default=3000)

    parser.add_argument("-sh", help="server host", default="localhost")
    parser.add_argument("-sp", help="server port", type=int, default=8007)
    args = parser.parse_args()

    f = open("logfile.txt", 'w')
    f.write("Logfile\n-------\n\n")
    f.close()

    # (todo) possibly break message up into n pckts

    # handshake with server (establish conn, determine window size)
    timeout = 3
    while True:
        try:
            print ("Sending handshake request to " + str(args.sh) + ":" + str(args.sp))
            peer_ip = ipaddress.ip_address(socket.gethostbyname(args.sh))
            conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            conn.settimeout(timeout)
            p = Packet(packet_type=3,
                       seq_num=0,
                       peer_ip_addr=peer_ip,
                       peer_port=args.sp,
                       payload=str(WINDOW_SIZE).encode("utf-8"))
            conn.sendto(p.to_bytes(), (args.rh, args.rp))
            response, sender = conn.recvfrom(1024)
            p = Packet.from_bytes(response)
            conn_port = p.payload.decode("utf-8")
            print ("Handshake accepted, connected to: " + conn_port)

            # append handshake info to logfile
            f = open("logfile.txt", 'a')
            f.write("Handshake accepted from local port {}, to server port {}".format(conn.getsockname(), conn_port))
            f.close()
            break

        except socket.timeout:
            print('No handshake response after {}s, trying again'.format(timeout))
            continue

    # init window_status and start sending pckts
    slide_window = threading.Condition()
    buffer_avail = threading.Condition()
    for seq in range(0, WINDOW_SIZE):
        window_status.append(seq)
        threading.Thread(target=send_udp_pkt, args=(args.rh, args.rp, peer_ip, conn_port,
                                                    conn, seq, slide_window, buffer_avail)).start()
        # send_udp_pkt(args.rh, args.rp, args.sh, args.sp)


if __name__ == "__main__":
    main()

