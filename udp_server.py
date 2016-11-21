import argparse
import socket
import threading
from random import randint
from collections import deque
import request_methods
import ProcessRequest
import sys
import os

from packet import Packet
M = 3
SEQUENCE_NUM_LIMIT = 2**M # not used any more
WINDOW_SIZE = 2**(M-1)

logfile = "server_logfile.txt"


# Initial thread dispatching for new clients, running on port 8007(default)
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


# handshake with new client and handle the back/forth on the designated port
def handshake_and_listen(data, sender):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = 60

    while True:
        try:
            # this thread gets ins own connection port
            port = randint(50000, 60000)
            conn.bind(('', port))

            # extract http request method, last_pkt seq# and window size from handshake packet
            p = Packet.from_bytes(data)
            payload = p.payload.decode("utf-8").split(":")
            method = payload[0]
            last_pkt = int(payload[1])
            WINDOW_SIZE = int(payload[2])

            # send handshake accept packet
            p.packet_type = 4  # handshake SYN
            p.payload = str(port).encode("utf-8")
            conn.sendto(p.to_bytes(), sender)

            # what threads (seq# being handled) are actively working
            window_status = deque()
            for i in range(0, WINDOW_SIZE):
                if i <= last_pkt:
                    window_status.append(i)
                else:
                    break
            # when threads receive a seq# other then the one they are looking for, buffer it
            msg_buffer = deque()
            request_processor = ProcessRequest.ProcessRequest(method)
            packets_list = []


            # thread locks and condistion to prevent data races between threads
            slide_window = threading.Condition()
            buffer_avail = threading.Condition()

            f = open(logfile, 'w')
            f.write("Server Logfile\n-------\n\n")
            f.close()

            print('Handshake pkt accepted , Server listening to client {} at port {}'.format(p.peer_port, port))
            while True:
                conn.settimeout(timeout)
                data, sender = conn.recvfrom(1024)
                threading.Thread(target=handle_client, args=(conn, data, sender, last_pkt, packets_list,
                                                             request_processor, window_status, msg_buffer,
                                                             slide_window, buffer_avail)).start()

        except socket.timeout:
            print('No response after {}s, timing out'.format(timeout))
            conn.close()
            break
        except OSError as e:
            print("OSError: ", e)
            conn.close()
            break
        except Exception as e:
            print("Handshake Error: ", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            conn.close()
            break


def handle_client(conn, data, sender, last_pkt, packets_list, request_processor,
                  window_status, waiting_pkts, slide_window, lock):
    try:
        terminate_thread = False
        p = Packet.from_bytes(data)

        p.packet_type = 1  # ACK
        print("Router: ", sender)
        print("Packet: ", p)
        print("Payload: ", p.payload.decode("utf-8"))

        # send ack
        conn.sendto(p.to_bytes(), sender)

        # if the packet has already been acked (out of window, or window empty), ack it again
        if len(window_status) > 0:
            if p.seq_num < window_status[0]:
                print ("Thread w/seq# {} is re-ACKed".format(p.seq_num))

            else:

                # if there's already a matching seq# waiting, just terminate
                # if not append to registered waiting packet threads
                while True:
                    have_lock = lock.acquire(0)
                    try:
                        if have_lock:
                            for i in waiting_pkts:
                                if i == p.seq_num:
                                    terminate_thread = True
                                    break

                    finally:
                        if have_lock:
                            if not terminate_thread:
                                waiting_pkts.append(p.seq_num)

                            lock.release()
                            break

                # skip this if this is a dup of a waiting packet
                if not terminate_thread:
                    with slide_window:
                        while p.seq_num != window_status[0]:
                            # else set this thread to wait
                            print ("Thread w/seq# {} is waiting to append.".format(p.seq_num))
                            print (window_status)
                            slide_window.wait()

                        # this thread is now oldest in window...
                        # append to request_str, slide window, remove from waiting pkts list
                        # and nofify all waiting threads
                        print ("Thread w/seq# {} is appending, sliding window".format(p.seq_num))
                        request_processor.add_to_request(p.payload.decode("utf-8"))
                        if p.seq_num < last_pkt:
                            window_status.append(window_status[-1]+1)
                        window_status.popleft()

                        while True:
                            have_lock = lock.acquire(0)
                            try:
                                if have_lock:
                                    for i in waiting_pkts:
                                        if i <= p.seq_num:
                                            waiting_pkts.remove(i)

                            finally:
                                if have_lock:
                                    lock.release()
                                    break

                        f = open(logfile, 'a')
                        f.write(p.payload.decode("utf-8") + "\n")
                        f.close()

                        slide_window.notifyAll()

    except Exception as e:
        print("Handle client Error: ", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

    if p.seq_num == last_pkt:
        while True:
            have_lock = lock.acquire(0)
            try:
                if have_lock:
                    print ("final thread finishing, string: " + request_processor.get_request())
                    # output to file
                    f = open(logfile, 'a')
                    f.write(str(window_status) + "\n" + str(waiting_pkts))
                    f.close()

                    # spawn threads to start sending the response
                    packets_list = request_methods.init_packet_list(packets_list, request_processor.process(), "")
                    last_pkt = len(packets_list) - 1

                    response_waiting_pkts = deque()
                    response_window_status = deque()
                    for i in range(0, WINDOW_SIZE):
                        if i <= last_pkt:
                            response_window_status.append(i)
                        else:
                            break

                    print ("{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n".format(sender, p.peer_ip_addr, p.peer_port,
                                                   conn, packets_list, last_pkt,
                                                   response_window_status, response_waiting_pkts))

                    #rehandshake and listen because client needs to know num packets in response
                    #todo rehandshake
                    #
                    #######
                    ###

                    for seq in range(0, WINDOW_SIZE):
                        if seq <= last_pkt:
                            window_status.append(seq)
                            threading.Thread(target=udp_send_response,
                                             args=(sender, p.peer_ip_addr, p.peer_port,
                                                   conn, seq, packets_list, last_pkt,
                                                   response_window_status, waiting_pkts, slide_window, lock)).start()
                        else:
                            break

            finally:
                if have_lock:
                    lock.release()
                    break
                else:
                    break


def udp_send_response(sender, peer_ip, peer_port, conn, seq,
                 packets_list, last_pkt, window_status, msg_buffer, slide_window, lock):
    print ("in sending udp response" + str(seq))
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
                                print("Found correct packet seq# " + seq_num + " in buffer")
                                rp = s
                                msg_buffer.remove(s)
                                resend = False
                finally:
                    if have_lock:
                        lock.release()
                        break

            if resend:
                print('Send packet ' + seq_num + ' and listen for ' + str(timeout) + 's')
                # create the packet
                p = Packet(packet_type=0,
                           seq_num=seq,
                           peer_ip_addr=peer_ip,
                           peer_port=peer_port,
                           payload=packets_list[seq].encode("utf-8"))

                # Send this packet out and start the timer for it
                conn.sendto(p.to_bytes(), sender)

                #########################################################
                #    program will wait here until receive or timeout    #
                #########################################################
                conn.settimeout(timeout)
                response, sender = conn.recvfrom(1024)
                # If a packet is received, check matching seq #
                rp = Packet.from_bytes(response)
                if rp.seq_num == seq:
                    print("Received correct packet # " + seq_num)
                    resend = False
                else:
                    print("Was expecting " + seq_num + ", but got " + str(rp.seq_num) +
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
                threading.Thread(target=udp_send_response(),
                                 args=(sender, peer_ip, peer_port, conn,
                                       packets_list[seq], next_seq,
                                       slide_window, lock)).start()

            while True:
                file_lock = lock.acquire(0)
                try:
                    if file_lock:
                        f = open(logfile, 'a')
                        f.write(rp.payload.decode("utf-8") + "\n")
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
        print ("final thread finished sending response")
        # output to file
        f = open(logfile, 'a')
        f.write("\n\n final packet sent abck to client \n" + str(window_status) + "\n" + str(msg_buffer))
        f.close()


def main():

    # Usage python udp_server.py [--port port-number]
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="echo server port", type=int, default=8007)
    args = parser.parse_args()
    run_server(args.port)


if __name__ == "__main__":
    main()
