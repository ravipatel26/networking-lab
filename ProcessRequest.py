#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket  # Networking support
import threading
import time  # Current time
import re
import os
import errno
from os import listdir
from os.path import isfile, join


class ProcessRequest:
    """ Class describing a simple HTTP server objects."""

    def __init__(self, method):
        """ Constructor """

        self.method = method
        self.request = ""

    def add_to_request(self, str):
        self.request += str

    def get_request(self):
        return self.request

    def _gen_headers(self, code, set_headers):
        """ Generates HTTP response Headers. Ommits the first line! """

        # determine response code

        h = ''
        if code == 200:
            h = 'HTTP/1.1 200 OK\n'
        elif code == 400:
            h = 'HTTP/1.1 400 Bad Request\n'
        elif code == 403:
            h = 'HTTP/1.1 403 Forbidden\n'
        elif code == 404:
            h = 'HTTP/1.1 404 Not Found\n'
        elif code == 405:
            h = 'HTTP/1.1 405 Method Not Allowed\n'
        elif code == 412:
            h = 'HTTP/1.1 412 Precondition Failed\n'
        elif code == 500:
            h = 'HTTP/1.1 500 File Access Permission Denided\n'

            # write further headers

        current_date = time.strftime('%a, %d-%b-%Y %H:%M:%S',
                                     time.localtime())
        h += 'Date: ' + current_date + '\n'
        h += 'Server: Simple-Python-HTTP-Server\n'
        h += 'Connection: close\n'  # signal that the conection wil be closed after complting the request
        for i in set_headers:
            h += i + '\n'

        return h + '\n'

    # ensure security of file string searched for.

    def is_requested_file_string_malicious(self, filename):
        # pattern = re.compile(r'\\').findall(filename)

        print(filename)
        if re.compile(r'\\').findall(filename) or re.compile(r'\.\.'
                                                             ).findall(filename):
            print('Found potentially harmful backslash(s) and/or periods')
            return True
        else:
            print('No potentially harmful backslashes or double periods found.')
            return False

    def process(self):
        print('Method: ' + self.method)
        print('Request body: ' + self.request)

        set_headers = []
        response_headers = ''
        response_content = ''

        # if method = get

        if self.method == 'GET':

            # file_requested = string[4:]

            # split on space "GET /file.html" -into-> ('GET','file.html',...)

            request_peices = self.request.split(' ')
            file_requested = request_peices[0]
            request_headers = ''

            if len(request_peices) > 1:
                request_headers = request_peices[1]

            # Check for URL arguments. Disregard them
            file_requested = file_requested.split('?')[0]  # disregard anything after '?'

            ''''# add the given headers
            if not request_headers == '' and not request_headers == '0':
                heads = request_headers.split('~')
                #todo
            '''

            # in case no file specified, get list of files on server
            print ("\'"+file_requested+"\'")

            if file_requested == '/':

                # file_requested = 'test.py' # load index.html by default

                dir_listing = [str(f.title() + '\n') for f in listdir('.')
                               if isfile(f)]
                print(dir_listing)
                set_headers.append('Content-Type:text/html')
                response_headers = self._gen_headers(200, set_headers)
                response_content = '  Directory Listing: \n'
                response_content += ''.join(dir_listing)
                print('Requesting the directory listing.')
            else:

                # User is requesting a file

                print('Requesting a file.')

                # remove first slash
                file_requested = file_requested.split('/', 1)[1]
                print('file requested: ' + file_requested)

                if self.is_requested_file_string_malicious(file_requested):
                    set_headers.append('Content-Type:text/html')
                    response_headers = self._gen_headers(403, set_headers)
                    response_content = "string: \'" + file_requested \
                                       + "\' permission denied. Outside of working directory."
                    print('send 403 Forbidden')
                else:
                    print('requested file string is secure.')

                    # if file exists on server

                    if os.path.isfile(file_requested):
                        try:
                            file_handler = open(file_requested, 'rb')
                            response_content = str(file_handler.read())  # read file content
                            file_handler.close()
                            set_headers.append('Content-Type: application/octet-stream'
                                               )
                            set_headers.append('Content-Disposition: attachment; filename="'
                                               + file_requested + '"')
                            response_headers = self._gen_headers(200,
                                                                 set_headers)
                        except IOError as ioex:
                            set_headers.append('Content-Type:text/html')
                            response_headers = self._gen_headers(500,
                                                                 set_headers)
                            response_content = \
                                'File access permission denied.: /' \
                                + file_requested
                            print('err code:' \
                                  + str(errno.errorcode[ioex.errno]) \
                                  + ', File access permission denied.')
                    else:

                        print("file: \'" + file_requested \
                              + "\' does not exist.")
                        set_headers.append('Content-Type:text/html')
                        response_headers = self._gen_headers(404,
                                                             set_headers)
                        response_content = "file: \'" + file_requested \
                                           + "\' does not exist."

            server_response = str(response_headers)  # return headers for GET and HEAD
            server_response += str(response_content)  # return additional conten for GET only

            return server_response

        elif self.method == 'POST':

            print('do POST')

            # split on space "GET /file.html data:data~qq:qq" ->into-> ('GET','file.html', datalist,...)

            request_elements = self.request.split(' ')

            # get 2nd element (filename and trim off beginning /slash)

            file_requested = request_elements[0]
            # remove first slash
            file_requested = file_requested.split('/', 1)[1]

            if self.is_requested_file_string_malicious(file_requested):
                response_content = "string: \'" + file_requested \
                                   + "\' is an insecure, bad characters detected."
                response_headers = self._gen_headers(400, set_headers)
                print('send 400 Bad Request')
            else:

                # isolate sent data and remove possible empties stemming from incorrect data format

                data = request_elements[2].split('~')
                data = [d for d in data if d != '']
                print('file requested and data list: ' + file_requested + str(data))

                overwrite = [d for d in data if d.lower()
                             == 'overwrite:true']
                if len(overwrite) > 0:
                    overwrite = True

                    # if file does NOT already exist OR overwrite is true, write to file.

                if not os.path.isfile(file_requested) or overwrite:
                    print('attempting to write to file...')
                    try:
                        file_handler = open(file_requested, 'w')
                        file_handler.write(self.request)
                        file_handler.close()
                        response_headers = self._gen_headers(200,
                                                             set_headers)
                        response_content = 'wrote to file: /' \
                                           + file_requested
                    except IOError as ioex:
                        response_headers = self._gen_headers(500,
                                                             set_headers)
                        response_content = \
                            ', File access permission denied.: /' \
                            + file_requested
                        print('err code:' \
                              + str(errno.errorcode[ioex.errno]) \
                              + 'File access permission denied.')
                else:

                    # 412 Precondition Failed, file exists, specify overwrite:true

                    response_headers = self._gen_headers(412, set_headers)
                    response_content = "File \'/" + file_requested \
                                       + "\' exists, specify overwrite:true"

            server_response = str(response_headers)  # return headers for GET and HEAD
            server_response += str(response_content) # return additional conten for GET only

            return server_response
        else:

            print('Unknown HTTP request method:' + self.method)
            server_response = str(self._gen_headers(405, set_headers))  # return headers for GET and HEAD
            server_response += str('Unknown HTTP request method:' + self.method) # return additional conten for GET only

            return server_response

