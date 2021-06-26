# UDP-chat-app

Instructions:

command (server mode): python3 UdpChat.py -s <port>
example: python3 UdpChat.py -s 2000

command (client mode): python3 UdpChat.py -c <name> <server-ip> <server-port> <client-port>
example: python3 UdpChat.py -c user1 198.123.75.45 2000 1024


Implementation notes:

Client and Server are two different classes that store 
their own pieces of socket information, as defined by the 
CLI arguments (using sys.arg).

Packets are stored as dictionaries, contain either strings or dictionaries, 
and are prepped as json objects.

SERVER implementation:

For storing client table information, 
I used a dictionary of dictionaries with the key being 
the client usernames and the second nested keys being 
"status", "IP", and "port".

The listen function runs indefinitely, until ctrl+c is called on it, 
Received packets are sent to handle_requests which sends an ACK
and then reads the message from the packet. 
If it is a specified request from a client,
("[REQUEST:XXXX]"), the server calls the appropriate methods.

Registration requests (reg/dereg) broadcast an updated table to all online clients.
If dereg, then it sends packet to client that requested it.

Server saves offline messages by appending to a text file in the format specified 
in assignment with timestamp.  When the saved messages are requested
upon signin, Server wipes the text file clean.

CLIENT implementation:

Client has two main running functions, which run on separate threads: listner and sender.
This is so that the client can simultaneously write and receive packets. 
Sender parses through whatever the user types and has a few specified commands (per the instructions).
Listener receives messages, updated tables, and ACKs.

Uses the same dictionary of dictionaries structure for local table.

Similar to server, it has several methods for different requests like req and .
All these requests use the send method which implements the "wait for ACK" feature.
Not sure if Client deals with every edge case, but tried to debug as many as I could.


Misc notes:
- if client x deregs and client x tries to send message, it will not send anything and warns user
- to quit client formally, type "ctrl + c". (>>> user: ctrl + c)
    * You can also use actual keyboard interruption ctrl+c but it is less clean.
- for server, use ctrl+c interruption; ctrl+z doesn't kill the process and port isn't freed; (it's not as clean as would've like it to be)
