# networking-lab 3
ARQ = Automatic Repeat reQuest(Query)

instructions to use:
- start the router in router/
- start the udp_server.py (with no args)
- use
    httpc.py get localhost:8007/filename

Theres just a few little bugs left to work out and then implement POST


todo:
- (optional) start server with httpc.py and reimplement the starting dir option

- improve comments and code readability, re-modulate code to my liking
- (from A2) correct parsing of the request should split on \r\n not the current ~
    this will make more compatible with curl

done:
- Setup initial udp client and server
- rebuild A1 httpc.py to work with udp
- how to send the packets through the router
- ensure client receives back all packets
- add thread waiting and notfying when earliest thread in window completes, to allow slide
- when a thread gets a other seq # buffer it and check if it's packet in buffer
    - set a thread lock on this buffer too
    - also check buffer when timeout
- check is seq number already in buffer when appending
- finish adding handshake server-side
    (packet_type: 0=data 1=ack 2=? 3=handshake_req 4=handshake_ACK 5=re-handshake_req 6=re-handshake_ACK)
- finish implementing handshake client-side
- added server sliding window?
- server-side is the one that needs to reorder packets
- incorporate my rdt with httpc and httpfs
- add client-side understanding of ACK? (kindof already does)
- client/and server need to validate data/AKS/HS_ACKs based on what theri expecting
    - remember the current RECEIVER side is always first to move to next phase
- the request string is not formatted properly on its way to through request_methods and to the server
- Client side problem with response window status
    potential sol: maybe not keep passing in a fresh window_status on each rec, yeah probably this, will fix
- implement POST



###############################################################
 # initial plan:
- implement the httpc client and httpfs file manager using UDP
- implement a specific instance of the Automatic-Repeat-Request ARQ
    - specifically Selective Repeat ARQ

- needs to mimic 3 way handshake
- understand how to add acks and nacks on top of UDP
- learn more about using wireshark

    udp message structure:
    1 byte:       packet type (data/ack/syn/syn-ack/NAK)
    4 bytes:      sequence # (big-endian)
    4 bytes:      peer address
    2 bytes:      peer port number
    < 1013 bytes: payload


 # What I'm learning
TCP is a 'stream oriented' protocol ensuring all data is transmitted in order
UDP is a 'message oriented' protocolUDP messages must
    fit within a single packet (for IPv4, that means they can only hold 65,507 bytes
    because the 65,535 byte packet also includes header information) and delivery
    is not guaranteed as it is with TCP.


In selective repeat, the window size must be less than or equal to
    1/2 the size of the sequence number space

Endianness...


 # dropped ideas
 see: dropped_ideas/

