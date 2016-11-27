import socket
import os
import os.path
import udp_client
import sys

CRLF = "\r\n\r\n"

# Printing out the correct version of the http protocol and the return status code
def print_response(r, v):
    # if verbose, print fancy headers and content, otherwise just the content
    if v:
        status = ""
        if r.raw.version == 10:
            status = "HTTP/1.0 "
        elif r.raw.version == 11:
            status = "HTTP/1.1 "
        else:
            status = "HTTP/2.0 "

        # print breadcrumbs if there were 30x redirects
        print (r.history)
        if r.history:
            print ("\nYou were redirected " + str(len(r.history)) + " times, here was your path:")
            for resp in r.history:
                print (status + str(resp.status_code) + " " + resp.url)
            print ("\nFinally: " + r.url)

        if r.status_code == 200:
            status += "200 OK"
            print ("\n" + status)

            #f = sys.stdout
            for e in r.headers:
                print (e + ": " + r.headers[e])

            '''print(status)
            print("Server: " + r.headers['Server'])
            print("Date: " + r.headers['Date'])
            print("Content-Type: " + r.headers['Content-Type'])
            print("Content-Length: " + r.headers['Content-Length'])
            #print("Connection: " + r.headers['Connection'])
            print("Access-Control-Allow-Origin: " + r.headers['Access-Control-Allow-Origin'])
            print("Access-Control-Allow-Credentials: " + r.headers['Access-Control-Allow-Credentials'])
            '''

    # print(r.content['args'])
    print(r.text)
    # print(r.json())


# parses the url (only for localhost (NOT ROBUST YET)) required format: host:port/[file]
# also cleans!
def parse_host_port(url):
    HOST = url.split(':', 1)[0]
    port_file = url.split(':', 1)[1]

    #PORT = re.findall(r'\d+', port_file)

    requested_file = '/'
    if url.count('/') >= 1:
        PORT = port_file.split('/', 1)[0]
        requested_file += port_file.split('/', 1)[1]
        requested_file = requested_file.replace(':', '') #clean out any colons from filename
    else:
        PORT = port_file
    return HOST, int(PORT), requested_file


def get(url, v, custom_headers):
    print("Using GET")
    if url.count(':') >= 1:
        HOST, PORT, requested_file = parse_host_port(url)
        print (HOST, PORT, requested_file)

    request = str(requested_file) + " " + str(custom_headers)

    udp_client.handshake_and_send(HOST, PORT, "GET", request, "")

    '''s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.settimeout(0.30)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # s.setblocking(0)
    s.connect((HOST, PORT))
    s.send(bytes("GET " + str(requested_file) + " " + str(custom_headers), 'utf8'))
    data = (s.recv(1000000))
    # print (data)
    # https://docs.python.org/2/howto/sockets.html#disconnecting
    s.shutdown(1)
    s.close()
    print ('\nReceived from server: \n' + str(repr(data)).replace("\\n", "\n"))

    #print_response(r, v)'''


def post(url, v, custom_headers, inline_data):
    print("Using POST")

    # r = requests.post(url, headers=custom_headers, data=json.dumps(data_dict))
    if url.count(':') >= 1:
        HOST, PORT, requested_file = parse_host_port(url)
        print (HOST, PORT, requested_file, inline_data)

    request = str(requested_file) + " " + str(inline_data)

    udp_client.handshake_and_send(HOST, PORT, "POST", request, "")

    ''''# r = requests.get(url, headers=custom_headers)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.30)

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # s.setblocking(0)
    s.connect((HOST, PORT))
    s.send(bytes("POST " + str(requested_file + " " + inline_data), 'utf8'))
    data = (s.recv(1000000))
    # print (data)
    # https://docs.python.org/2/howto/sockets.html#disconnecting
    s.shutdown(1)
    s.close()
    print ('\nReceived from server: \n' + str(repr(data)).replace("\\n", "\n"))

    #print_response(r, v)'''


# initialize our list of packets to send
def init_packet_list(packets_list, request, infile):

    current_payload = ""
    for ch in request:
        if sys.getsizeof(current_payload) < 1010:
            current_payload += ch
        else:
            packets_list.append(current_payload)
            current_payload = ch

    if len(current_payload) > 0:
        packets_list.append(current_payload)

    '''if len(packets_list) > 0:
        # just add spaces at beginning and end for splitting at server
        packets_list[0] = " " + str(packets_list[0])
        packets_list[-1] = " " + str(packets_list[-1])'''

    if os.path.isfile(infile):
        print ("is file?")
        with open(infile, 'rb') as i:
            while True:
                chunk = i.read(1012)
                if chunk:
                    print (chunk)
                    packets_list.append(chunk)
                else:
                    break
        # i.close()

    print ("Finished init_packet_list, num packets: " + str(len(packets_list)))
    return packets_list
