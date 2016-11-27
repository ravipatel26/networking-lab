import argparse
import ipaddress
import socket
import threading
from collections import deque
import request_methods
import ProcessRequest
import sys
import os


from packet import Packet
M = 3
SEQUENCE_NUM_LIMIT = 2**M # not used anymore, never-ending sequence
WINDOW_SIZE = 2**(M-1)

window_status = deque()
msg_buffer = deque()

logfile = "logfile.txt"


def handshake_and_send(HOST, PORT, method, request, infile):
    # Usage:
    # python echoclient.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007

    routerhost = "localhost"
    routerport = 3000
    serverhost = HOST
    serverport = PORT
    response_processor = ProcessRequest.ProcessRequest("Response")

    l = open(logfile, 'w')
    l.write("Logfile\n-------\n\n")
    l.close()

    # (todo) possibly break message up into n pckts
    # init window_status and start sending pckts
    slide_window = threading.Condition()
    buffer_avail = threading.Condition()
    # initialize our list of packets to send
    packets_list = []
    request_methods.init_packet_list(packets_list, request, infile)
    last_pkt = len(packets_list) - 1

    # handshake with server (establish conn, determine window size)
    timeout = 3
    while True:
        try:
            print ("Sending handshake request to " + str(serverhost) + ":" + str(serverport))
            peer_ip = ipaddress.ip_address(socket.gethostbyname(serverhost))
            conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            conn.settimeout(timeout)
            p = Packet(packet_type=3,
                       seq_num=0,
                       peer_ip_addr=peer_ip,
                       peer_port=serverport,
                       payload=(method + ":" + str(last_pkt) + ":" + str(WINDOW_SIZE)).encode("utf-8"))
            conn.sendto(p.to_bytes(), (routerhost, routerport))
            response, sender = conn.recvfrom(1024)
            p = Packet.from_bytes(response)
            conn_port = p.payload.decode("utf-8")
            print ("Handshake accepted, connected to: " + conn_port)

            # append handshake info to logfile
            l = open(logfile, 'a')
            l.write("Handshake accepted from local port {}, to server port {}\n".format(conn.getsockname(), conn_port))
            l.close()
            break

        except socket.timeout:
            print('No handshake response after {}s, trying again'.format(timeout))
            continue

    for r in packets_list:
        print (sys.getsizeof(r))
    print (packets_list)

    for seq in range(0, WINDOW_SIZE):
        if seq <= last_pkt:
            window_status.append(seq)
            threading.Thread(target=send_udp_pkt, args=(routerhost, routerport, peer_ip, conn_port,
                                                        conn, seq, packets_list, last_pkt, response_processor,
                                                        slide_window, buffer_avail)).start()
        else:
            break


def send_udp_pkt(router_addr, router_port, peer_ip, server_port,
                 conn, seq, packets_list, last_pkt, response_processor,
                 slide_window, lock):
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
                           payload=packets_list[seq].encode("utf-8"))

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

        # Only the oldest thread is allowed to complete first the others must wait
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
                                 args=(router_addr, router_port, peer_ip, server_port, conn,
                                       next_seq, packets_list, last_pkt, response_processor,
                                       slide_window, lock)).start()

            while True:
                file_lock = lock.acquire(0)
                try:
                    if file_lock:
                        f = open(logfile, 'a')
                        f.write(p.payload.decode("utf-8") + "\n")
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

        while True:
            have_lock = lock.acquire(0)
            try:
                if have_lock:
                    print ("final thread finished sending request, expecting re-handshake for response length")
                    # output to file
                    f = open(logfile, 'a')
                    f.write(str(window_status) + "\n" + str(msg_buffer))
                    f.close()

                    response_window_status = deque()
                    waiting_pkts = deque()
                    response_queue_lock = threading.Condition()

                    # print ("{}\n{}\n{}\n{}\n{}\n".format(conn, sender, last_pkt, window_status, response_msg_buffer))

                    #todo expect a handshake packet
                    print("waiting for re-handshake packet...")

                    shook = False
                    timeout = 30
                    conn.settimeout(timeout)
                    while True:
                        try:
                            data, sender = conn.recvfrom(1024)
                            p = Packet.from_bytes(data)

                            print("Router: ", sender)
                            print("Response Packet Type: ", p.packet_type)
                            print("Packet: ", p)
                            #print("Payload: ", p.payload.decode("utf-8"))
                            #print ("response_window_status: ")
                            #print (response_window_status)

                            # if handshake request, just send handshake ack
                            if p.packet_type == 5:
                                if not shook:
                                    shook = True
                                    last_pkt = int(p.payload.decode("utf-8"))
                                    for seq in range(0, WINDOW_SIZE):
                                        if seq <= last_pkt:
                                            response_window_status.append(seq)

                                p.packet_type = 6
                                conn.sendto(p.to_bytes(), sender)
                            # if response data, handle it
                            elif p.packet_type == 0:
                                if shook:
                                    # handle response packet
                                    threading.Thread(target=handle_server_response, args=(conn, p, sender, last_pkt, response_processor,
                                                                                          response_window_status, waiting_pkts,
                                                                                            slide_window, response_queue_lock)).start()

                        except socket.timeout:
                            print('No response packets after {}s, timing out'.format(timeout))
                            break
                        continue

            finally:
                if have_lock:
                    lock.release()
                    break
                else:
                    break


def handle_server_response(conn, p, sender, last_pkt, response_processor,
                           response_window_status, waiting_pkts, slide_window, lock):

    terminate_thread = False

    try:

        seq = p.seq_num
        payload = p.payload.decode("utf-8")

        # send ACK
        a = p
        a.packet_type = 1
        a.payload = ''.encode()
        conn.sendto(a.to_bytes(), sender)

        # if the packet has already been acked (out of window, or window empty), ack it again
        if len(response_window_status) > 0:
            if seq < response_window_status[0]:
                print ("Thread w/seq# {} is dup, just kill".format(seq))

            else:

                # if there's already a matching seq# waiting, just terminate
                # if not append to registered waiting packet threads
                while True:
                    have_lock = lock.acquire(0)
                    try:
                        if have_lock:
                            if seq in waiting_pkts:
                                terminate_thread = True

                    finally:
                        if have_lock:
                            if not terminate_thread:
                                waiting_pkts.append(seq)

                            lock.release()
                            break

                # skip this if this is a dup of a waiting packet
                if not terminate_thread:
                    with slide_window:
                        # if youre still waiting for packets
                        if len(response_window_status) > 0:
                            while seq != response_window_status[0]:
                                # else set this thread to wait
                                print ("Thread w/seq# {} is waiting to append.".format(seq))
                                print (waiting_pkts)
                                print (response_window_status)
                                slide_window.wait()
                        else:
                            # you're not waiting for packets anymore
                            terminate_thread = True
                            slide_window.notifyAll()

                        if not terminate_thread:
                            # this thread is now oldest in window...
                            # append to request_str, slide window, remove from waiting pkts list
                            # and nofify all waiting threads
                            print ("Thread w/seq# {} is appending, sliding window".format(seq))
                            response_processor.add_to_request(payload)
                            if seq < last_pkt and response_window_status[-1] != last_pkt:
                                response_window_status.append(response_window_status[-1]+1)
                            response_window_status.popleft()

                            print ("response_window_status: ")
                            print (response_window_status)

                            while True:
                                have_lock = lock.acquire(0)
                                try:
                                    if have_lock:
                                        for i in waiting_pkts:
                                            if i <= seq:
                                                waiting_pkts.remove(i)

                                finally:
                                    if have_lock:
                                        lock.release()
                                        break

                            f = open(logfile, 'a')
                            f.write("\nHere is the response payload: \n" + payload + "\n")
                            f.close()

                            # wake any sleeping threads to see if now its their turn to finish
                            slide_window.notifyAll()

                            l = open(logfile, 'a')
                            l.write("Response logs: \n current seq# {}, final pkt# {}\n".format(seq, last_pkt))
                            l.close()

                            if seq == last_pkt:
                                print ("\nfinal thread finishing, response: \n" + response_processor.get_request())
                                # output to file
                                f = open(logfile, 'a')
                                f.write(str(response_window_status) + "\n" + str(waiting_pkts))
                                f.close()

    except Exception as e:
        print("Handle client Error: ", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)




