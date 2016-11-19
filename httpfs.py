import argparse
from Server import Server
import signal  # Signal support (server shutdown on signal receive)
import os
import re


def graceful_shutdown(sig, dummy):
    """ This function shuts down the server. It's triggered
    by SIGINT signal """
    s.shutdown() #shut down the server
    import sys
    sys.exit(1)

###########################################################
# shut down on ctrl+c
signal.signal(signal.SIGINT, graceful_shutdown)

print ("Starting web server")
# Usage: python3 test.py -host host -p port
parser = argparse.ArgumentParser()
parser.add_argument("-v", help="Verbose?", action='store_true')
parser.add_argument("-p", help="Server Port", type=int, default=9000)
parser.add_argument("-d", help="Working Directory", type=str, default='.')
args = parser.parse_args()

# make sure specified working directory exists and not moving up directories
if re.compile(r'\.\.').findall(args.d):
    print ("Working directory should never go up..")
elif not os.path.exists(args.d):
    print ("working directory sub-directory does not exist.")
else:
    s = Server(args.v, args.p, args.d) # construct server object
    s.activate_server() # aquire the socket
