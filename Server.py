import socket  # Networking support
import threading
import time    # Current time
import re
import os, errno
from os import listdir
from os.path import isfile, join

class Server:
 """ Class describing a simple HTTP server objects."""

 def __init__(self, v, port, dir):
     """ Constructor """
     self.host = 'localhost'   # <-- works on all avaivable network interfaces
     self.port = port
     self.v = v
     os.chdir(dir)
     self.www_dir = dir # Directory where webpage files are stored

 def vPrint(self, m):
     if self.v:
         print (m)

 def activate_server(self):
     """ Attempts to aquire the socket and launch the server """
     self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     try: # user provided in the __init__() port may be unavaivable
         self.vPrint("Launching HTTP server on " + self.host + ":" + self.port)
         self.socket.bind((self.host, self.port))

     except Exception as e:
         self.vPrint ("Warning: Could not aquite port: " + str(self.port) + "\n")
         self.vPrint ("Trying a higher port")
         # store to user provideed port locally potentiallly for later
         user_port = self.port
         self.port = 9001

         try:
             self.vPrint("Launching HTTP server on " + self.host + ":" + str(self.port))
             self.socket.bind((self.host, self.port))

         except Exception as e:
             self.vPrint("ERROR: Failed to acquire sockets for ports " + str(user_port) + " and " + str(self.port))
             self.vPrint("Try running the Server in a privileged user mode.")
             self.shutdown()
             import sys
             sys.exit(1)

     print ("Server successfully acquired the socket with port:", self.port)
     self.vPrint ("Press Ctrl+C to shut down the server and exit.")
     self._wait_for_connections()

 def shutdown(self):
     """ Shut down the server """
     try:
         print("Shutting down the server")
         s.socket.shutdown(socket.SHUT_RDWR)

     except Exception as e:
         self.vPrint("Warning: could not shut down the socket. Maybe it was already closed?" + str(e))

 def _gen_headers(self,  code, set_headers):
     """ Generates HTTP response Headers. Ommits the first line! """

     # determine response code
     h = ''
     if (code == 200):
        h = 'HTTP/1.1 200 OK\n'
     elif (code == 400):
        h = 'HTTP/1.1 400 Bad Request\n'
     elif (code == 403):
        h = 'HTTP/1.1 403 Forbidden\n'
     elif (code == 404):
        h = 'HTTP/1.1 404 Not Found\n'
     elif (code == 405):
        h = 'HTTP/1.1 405 Method Not Allowed\n'
     elif (code == 412):
        h = 'HTTP/1.1 412 Precondition Failed\n'
     elif (code == 500):
        h = 'HTTP/1.1 500 File Access Permission Denided\n'

     # write further headers
     current_date = time.strftime("%a, %d-%b-%Y %H:%M:%S", time.localtime())
     h += 'Date: ' + current_date +'\n'
     h += 'Server: Simple-Python-HTTP-Server\n'
     h += 'Connection: close\n'  # signal that the conection wil be closed after complting the request
     for i in set_headers:
         h += i + "\n"

     return h + "\n"

#ensure security of file string searched for.
 def is_requested_file_string_malicious(self, filename):
     #pattern = re.compile(r'\\').findall(filename)
     self.vPrint (filename)
     if re.compile(r'\\').findall(filename) or re.compile(r'\.\.').findall(filename):
         self.vPrint('Found potentially harmful backslash(s) and/or periods')
         return True
     else:
         self.vPrint('No potentially harmful backslashes or double periods found.')
         return False

 def listen_to_client(self, conn, addr):
     self.vPrint("Got connection from:" + str(addr))

     data = conn.recv(1024)  # receive data from client
     self.vPrint(data)
     string = bytes.decode(data)  # decode it to string

     # determine request method  (HEAD and GET are supported)
     request_method = string.split(' ')[0]
     self.vPrint("Method: " + request_method)
     self.vPrint("Request body: " + string)

     set_headers = []
     response_headers = ""
     response_content = ""

     # if method = get
     if (request_method == 'GET'):
         # file_requested = string[4:]

         # split on space "GET /file.html" -into-> ('GET','file.html',...)
         request_string = string.split(' ')
         file_requested = request_string[1]  # get 2nd element
         request_headers = ""

         if len(request_string) > 2:
             request_headers = request_string[2]


         # Check for URL arguments. Disregard them
         file_requested = file_requested.split('?')[0]  # disregard anything after '?'

         # in case no file specified, get list of files on server
         if (file_requested == '/'):
             # file_requested = 'test.py' # load index.html by default
             dir_listing = [str(f.title() + "\n") for f in listdir('.') if isfile(f)]
             self.vPrint(dir_listing)
             '''#file_requested = self.www_dir + file_requested
             print ("Serving web page [",file_requested,"]")'''
             set_headers.append("Content-Type:text/html")
             response_headers = self._gen_headers(200, set_headers)
             response_content = '  Directory Listing: \n'
             response_content += ''.join(dir_listing)
             self.vPrint("Requesting the directory listing.")

             # User is requesting a file
         else:
             self.vPrint("Requesting a file.")
             # remove first slash
             file_requested = file_requested.split('/', 1)[1]
             # clean desired filename for security
             if self.is_requested_file_string_malicious(file_requested):
                 set_headers.append("Content-Type:text/html")
                 response_headers = self._gen_headers(403, set_headers)
                 response_content = "string: \'" + file_requested + "\' permission denied. Outside of working directory."
                 self.vPrint("send 403 Forbidden")
             else:
                 self.vPrint("requested file string is secure.")
                 # if file exists on server
                 if (os.path.isfile(file_requested)):
                     try:
                         file_handler = open(file_requested, 'rb')
                         response_content = str(file_handler.read())  # read file content
                         file_handler.close()
                         set_headers.append("Content-Type: application/octet-stream")
                         set_headers.append("Content-Disposition: attachment; filename=\"" + file_requested + "\"")
                         response_headers = self._gen_headers(200, set_headers)
                     except IOError as ioex:
                         set_headers.append("Content-Type:text/html")
                         response_headers = self._gen_headers(500, set_headers)
                         response_content = "File access permission denied.: /" + file_requested
                         self.vPrint(
                             "err code:" + str(errno.errorcode[ioex.errno]) + ", File access permission denied.")

                 else:
                     self.vPrint("file: \'" + file_requested + "\' does not exist.")
                     set_headers.append("Content-Type:text/html")
                     response_headers = self._gen_headers(404, set_headers)
                     response_content = "file: \'" + file_requested + "\' does not exist."

                     '''print ("Warning, file not found. Serving response code 404\n", e)
                     response_headers = self._gen_headers(404)
                     response_content = b"<html><body><p>Error 404: File not found</p><p>Python HTTP server</p></body></html>"
                     '''
         server_response = response_headers.encode()  # return headers for GET and HEAD
         server_response += bytes(response_content, 'utf8')  # return additional conten for GET only

         conn.send(server_response)
         self.vPrint("Closing connection with client")
         conn.close()

     elif (request_method == 'POST'):
         self.vPrint("do POST")

         # split on space "GET /file.html data:data~qq:qq" ->into-> ('GET','file.html', datalist,...)
         request_elements = string.split(' ')
         # get 2nd element (filename and trim off beginning /slash)
         file_requested = request_elements[1].split('/', 1)[1]

         if self.is_requested_file_string_malicious(file_requested):
             response_content = "string: \'" + file_requested + "\' is an insecure, bad characters detected."
             response_headers = self._gen_headers(400, set_headers)
             self.vPrint("send 400 Bad Request")
         else:
             # isolate sent data and remove possible empties stemming from incorrect data format
             data = request_elements[2].split('~')
             data = [d for d in data if d != '']
             self.vPrint("file requested and data list: " + file_requested + str(data))

             overwrite = [d for d in data if d.lower() == 'overwrite:true']
             if len(overwrite) > 0:
                 overwrite = True

             # if file does NOT already exist OR overwrite is true, write to file.
             if not os.path.isfile(file_requested) or overwrite:
                 self.vPrint("attempting to write to file...")
                 try:
                     file_handler = open(file_requested, 'w')
                     print (string, file=file_handler)
                     file_handler.close()
                     response_headers = self._gen_headers(200, set_headers)
                     response_content = "wrote to file: /" + file_requested
                 except IOError as ioex:
                     response_headers = self._gen_headers(500, set_headers)
                     response_content = ", File access permission denied.: /" + file_requested
                     self.vPrint("err code:" + str(errno.errorcode[ioex.errno]) + "File access permission denied.")

             else:
                 # 412 Precondition Failed, file exists, specify overwrite:true
                 response_headers = self._gen_headers(412, set_headers)
                 response_content = "File \'/" + file_requested + "\' exists, specify overwrite:true"

         server_response = response_headers.encode()  # return headers for GET and HEAD
         server_response += bytes(response_content, 'utf8')  # return additional conten for GET only

         conn.send(server_response)
         self.vPrint("Closing connection with client")
         conn.close()

     else:
         self.vPrint("Unknown HTTP request method:" + request_method)
         server_response = self._gen_headers(405, set_headers).encode()  # return headers for GET and HEAD
         server_response += bytes("Unknown HTTP request method:" + request_method,
                                  'utf8')  # return additional conten for GET only

         conn.send(server_response)
         self.vPrint("Closing connection with client")
         conn.close()

 def _wait_for_connections(self):
     """ Main loop awaiting connections """
     self.socket.listen(5) # maximum number of queued connections
     while True:
         self.vPrint ("Awaiting New connection")

         conn, addr = self.socket.accept()
         # conn - socket to client
         # addr - clients address
         conn.settimeout(60)
         threading.Thread(target=self.listen_to_client(conn, addr), args=(conn, addr)).start()
