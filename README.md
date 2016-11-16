# networking-lab 3

todo:
- understand how to add acks and nacks on top of UDP
- how to send the packets through the router
- learn more about using wireshark

- improve comments and code readability
- (from A2) correct parsing of the request should split on \r\n not the current ~
    this will make compatible with curl

done:
- Setup initial udp client and server
- rebuild A1 httpc.py to work with udp



###############################################################
 # initial plan:
- implement the httpc client and httpfs file manager using UDP
- implement a specific instance of the Automatic-Repeat-Request ARQ
    - specifically Selective Repeat ARQ

- needs to mimic 3 way handshake

    udp message structure:
    1 byte:       packet type (data/ack/syn/syn-ack/NAK)
    4 bytes:      sequence # (big-endian)
    4 bytes:      peer address
    2 bytes:      peer port number
    < 1013 bytes: payload






 # Things i'm learning
TCP is a 'stream oriented' protocol ensuring all data is transmitted in order
UDP is a 'message oriented' protocolUDP messages must
    fit within a single packet (for IPv4, that means they can only hold 65,507 bytes
    because the 65,535 byte packet also includes header information) and delivery
    is not guaranteed as it is with TCP.


In selective repeat, the window size must be less than or equal to
    1/2 the size of the sequence number space

Endianness...


 # dropped ideas

