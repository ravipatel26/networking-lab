# networking-lab

todo:
- improve comments and code readability
- correct parsing of the request should split on \r\n not the current ~
    - this will make compatible with curl

done:
- understand using bare sockets for server-client interaction
- implement get to see server directory listing
- rebuild A1 httpc.py to work without requests
- implement get to see server file contents
- implement post to write to a file on server
- add working directory commmand line arg
- add bonus header stuff
- support multithreading



###############################################################
 # dropped ideas

'''This just replaces insecurities in requestedfile string, but I removed
it because I need to send 400 bad request if this is happenning'''
 def secure_file_requested_string(self, filename):
     # first remove all potentially malicious specialcharacters
     filename = re.sub('[^A-Za-z0-9\.]+', '', filename)
     # ensure no double periods for potential malicious directory changes
     filename = re.sub('[\.]+', '.', filename)
     print ("cleaned filename: " + filename)
     return filename