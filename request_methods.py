import json
import socket
import os
import re

CRLF = "\r\n\r\n"

# Printing out the correct version of the http protocol and the return status code
def print_response(r, v, fh):
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
        print (r.history, file=fh)
        if r.history:
            print ("\nYou were redirected " + str(len(r.history)) + " times, here was your path:", file=fh)
            for resp in r.history:
                print (status + str(resp.status_code) + " " + resp.url, file=fh)
            print ("\nFinally: " + r.url, file=fh)

        if r.status_code == 200:
            status += "200 OK"
            print ("\n" + status)

            #f = sys.stdout
            for e in r.headers:
                print (e + ": " + r.headers[e], file=fh)

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
    print(r.text, file=fh)
    # print(r.json())

    fh.close()


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


def get(url, v, custom_headers, outfile):
    print("Using GET", file=outfile)
    if url.count(':') >= 1:
        HOST, PORT, requested_file = parse_host_port(url)
        print (HOST, PORT, requested_file)

    # GET the URL  <--------
    # r = requests.get(url, headers=custom_headers)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """
    ***********************************************************************************
    * Note that the connect() operation is subject to the timeout setting,
    * and in general it is recommended to call settimeout() before calling connect()
    * or pass a timeout parameter to create_connection().
    * The system network stack may return a connection timeout error of its own
    * regardless of any Python socket timeout setting.
    ***********************************************************************************
    """
    s.settimeout(0.30)
    """
    **************************************************************************************
    * Avoid socket.error: [Errno 98] Address already in use exception
    * The SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state,
    * without waiting for its natural timeout to expire.
    **************************************************************************************
    """
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

    #print_response(r, v, outfile)


def post(url, v, custom_headers, inline_data, outfile):
    print("Using POST", file=outfile)

    # r = requests.post(url, headers=custom_headers, data=json.dumps(data_dict))
    if url.count(':') >= 1:
        HOST, PORT, requested_file = parse_host_port(url)
        print (HOST, PORT, requested_file, inline_data)

    # r = requests.get(url, headers=custom_headers)

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
    print ('\nReceived from server: \n' + str(repr(data)).replace("\\n", "\n"), file=outfile)

    #print_response(r, v, outfile)
