#!/usr/bin/python3
from socket import *
import sys
import json
import threading 
import os
import time
import datetime 
import sys

class Client:
    def __init__(self, client_name, server_ip, server_port, client_port):
        # constructor
        self.client_name = client_name
        self.server_ip = server_ip
        self.server_port = int(server_port)
        self.client_ip = gethostbyname(gethostname())
        self.client_port = int(client_port)
        self.clientSocket = socket(AF_INET, SOCK_DGRAM)
        self.local_table = {} # for storing client table
        self.quit = False # for dealing with threading listener and sender threads  
        self.ACK = False # for dealing with ack receiving
        
    # helper methods to make life easier
    def textLine(self, x):
        # for aesthetic CLI format
        return "\n>>> {}".format(x)

    def make_packet(self, x):
        packet = {"message": x} 
        return bytearray(json.dumps(packet), "utf-8")
    def unpack_packet(self,packet):
        return json.loads(packet)
    
    def send_ack(self, client_ip, client_port):
        ack = self.make_packet("ACK")
        self.clientSocket.sendto(ack, (client_ip, client_port))

    def is_existing_client(self, client_name):
        # for checking if client in local table  
        if client_name in self.local_table.keys():
            return True
        else:
            return False
    
    # request functions
    def register(self):
        """
        When called, will look to see if local table has its entry (i.e. if it's registering for first time)
        If it already exists then it will request any saved messages from the server if it was deregistered.
        It will send registration request to server.
        """
        # check if user already exists in local table
        exist = self.is_existing_client(self.client_name)
        if exist==False:
            # for first registration
            self.local_table[self.client_name] = {"IP":self.client_ip, "port":self.client_port, "status":True}
        # else:
        #     # for updating status of user 
        #     self.local_table[self.client_name]["status"]=True
        # request is boolean : True if request went throug, ow False
        request = self.send("[REQUEST:REG] {}".format(self.client_name),"server")
        if request==True and exist==True:
            request = self.send("[REQUEST:GETSAVE] {}".format(self.client_name),"server")
            print(self.textLine("[Welcome back, {}.]".format(self.client_name)))
        elif request==True and exist==False:
            print(self.textLine("[Welcome, you are now registered.]"))
        elif request==False:
            print(self.textLine("[Server not responding]"))
            print(self.textLine("[Exiting]"))
            # self quit is for dealing with threads for listener and sender
            


    def deregister(self):
        """
        Will set its local table entry for status to false and send dergistration request to server.
        """
        # self.local_table[self.client_name]["status"]=False
        request = self.send("[REQUEST:DEREG] {}".format(self.client_name),"server")
        if request==True:
            print(self.textLine("[You are Offline. Bye.]"))
        else:
            print(self.textLine("[Server not responding]"))
            print(self.textLine("[Exiting]"))
            

    def send_to_client(self,message, to):
        """
        For sending messages from A to client B.
        If the B has online status, then it will send message and wait for ACK on listener.
        If there is no ACK or B is offline, then the message gets sent with a Save request to the server.
        If B doesn't exist on the local table, then it doesn't send anything and tells the user.
        """
        if self.local_table[self.client_name]["status"]==True:

            if self.is_existing_client(to):

                if self.local_table[to]["status"] == True:
                    request = self.send(message,to)
                    if request==False:
                        print(self.textLine("[No ACK from {}, message sent to server.]".format(to)))
                        message_edit = " ".join(message.split(" ")[1:])
                    
                        self.send("[REQUEST:SAVE] {} {} {}".format(self.client_name, to, message_edit),"server")
                else:
                    print("[Client {} is offline, message sent to server.]".format(to))
                    message_edit = " ".join(message.split(" ")[1:])
                    
                    request =self.send("[REQUEST:SAVE] {} {} {}".format(self.client_name, to, message_edit),"server")
                    if request == True:
                        print(self.textLine("[Messages received by the server and saved]\n>>> "),end="")
                    else:
                        print(self.textLine("[Server not responding]"))
                        print(self.textLine("[Exiting]"))
            else:
                print(self.textLine("[{} not in local table]".format(to)))
        else:
            print(self.textLine("[Can't send message, you are offline.]"))
    def send(self,  message, to):
        """
        Sends a stringed message from client A to either server or B.
        If to="server", then it just sends message to server.
        Otherwise it sends to a clientname based on info from local table.
        Implements the wait for ACK part, but the actual ACK is set by self.ACK 
        in constructor, which is updated in listener.

        Returns True if message went through and ACKed, False if it failed 5 times.
        """
        dest_ip = None
        dest_port =None
        dest_status=None
        if to != "server": # if sending to another client
            if self.is_existing_client(to):
                dest_ip = self.local_table[to]["IP"]
                dest_port = self.local_table[to]["port"]
                dest_status = self.local_table[to]["status"]
            else:
                print(self.textLine("[{} not in local table]".format(to)),end="")
                return False
        else: # if sending to server
            dest_ip = self.server_ip
            dest_port = self.server_port
        packet = self.make_packet(message)
        fails = 1
        # waiting for ACK
        while fails <5:
            self.ACK = False
            self.clientSocket.sendto(packet, (dest_ip, dest_port)) 
            start_time = time.time()
            # time out for 500ms
            while True:
                if 1000*(time.time()-start_time) >500 or self.ACK==True:
                    break
            if self.ACK==True:
                break
            else: 
                fails+=1 
        if fails ==5:
            return False
        else:
            return True

    def sender(self):
        """
        Handles all user input. 
        """
        #initial registration
        
        
        self.register()
        if self.quit==True:
            self.clientSocket.close()
            return None
        message = input("\n>>> {}: ".format(self.client_name))
        while True:
            try:
                message_split = message.split(" ")
                if message=="ctrl + c":
                    self.quit=True
                if message_split[0]=="send":# send to client
                    full_message = self.client_name+": "+" ".join(message_split[2:])
                    self.send_to_client(full_message, message_split[1]) 
                elif message_split[0]=="reg":# registration
                    if message_split[1]==self.client_name:
                        self.register()
                    else: 
                        print(self.textLine("[Cannot register {}]".format(message_split[1])))
                elif message_split[0]=="dereg" and message_split[1]==self.client_name: # deregistration
                    if message_split[1]==self.client_name:
                        self.deregister()
                    else: 
                        print(self.textLine("[Cannot deregister {}]".format(message_split[1])))
                if self.quit:
                    break
                message = input("\n>>> {}: ".format(self.client_name))
            except : 
                print("\nCLIENT CLOSING...")
                break
        
        self.clientSocket.close()
        return None 
    def listener(self):
        """
        Listens and responds to all incoming packets.
        """
        
        
        while True:
            try:
           
                dest_packet, destAddress = self.clientSocket.recvfrom(4096)
                dest_message = self.unpack_packet(dest_packet)["message"]
             
                if self.quit:
                    break
             
                if dest_message is not None:
                        # ack 
                    if dest_message=="ACK":
                        self.ACK=True # this is how the send() gets ACK 
                            # ack from client
                        if destAddress[0]!=self.server_ip or destAddress[1]!=self.server_port:
                            to = None
                            for k, v in self.local_table.items():
                                if v["IP"]==destAddress[0] and v["port"]==destAddress[1]:
                                    to =k
                            print(self.textLine("[Messsage received by {}]".format(to)),end="")
                            # ack from server
                        
                        # non-ack message
                    else:
                            # if message is table from server
                        if type(dest_message) is dict :
                            if dest_message!=self.local_table:
                                print(self.textLine("[Client table updated.]"),end="")
                                print(self.textLine(self.client_name +": "),end="")
                                self.local_table=dest_message

                        else:
                            if destAddress[0]!=self.server_ip or destAddress[1]!=self.server_port:
                                    # if message from client, send ack
                                self.send_ack(destAddress[0],destAddress[1])
                                
                            if dest_message.split(" ")[0] != "[REQUEST:SAVE]":
                                print(self.textLine(dest_message),end="")
                                print(self.textLine(self.client_name +": "),end="")
            except:
                break
        return None   

    def run(self):
        
        # main running function
        # used threading to allow for constant listening, so that when server updates
        # all clients can receive update
        t1 = threading.Thread(target=self.sender) 
        t2 = threading.Thread(target=self.listener)
        t1.start()
        t2.start()
        
class Server:
    def __init__(self, listeningPort=12000):
        
        self.listeningPort = listeningPort
        self.serverSocket = socket(AF_INET, SOCK_DGRAM)
        self.serverSocket.bind(("", self.listeningPort))
        self.client_table ={}
        self.duplicate =False

    def make_packet(self, message):
        return bytearray(json.dumps(message), "utf-8")

    def unpack_packet(self,packet):
        return json.loads(packet)

    def broadcast(self, packet, clients):
        # to broadcast to a set of given client names
  
        for client in clients:
            client_ip = self.client_table[client]["IP"]
            client_port = self.client_table[client]["port"]
            client_status = self.client_table[client]["status"]
            if client_status==True:
                # CLIENT ONLINE : SEND TO CLIENT
                self.serverSocket.sendto(packet, (client_ip, client_port) )
            
    def is_existing_client(self, client_name, client_ip, client_port):
        # for checking table in server 
        # IS_EXISTING_CLIENT...
        if client_name in self.client_table.keys() :
            # Name exists in table
            # Checking if duplicate...
            table_client_ip = self.client_table[client_name]["IP"] 
            table_client_port = self.client_table[client_name]["port"]
            # check if the ip and port are the same under the same name
            if client_ip == table_client_ip and table_client_port == client_port:
                
                return True
            # if different, will treat as duplicate
            else:
                self.duplicate = True
                return True
        else:
            return False
    
    def sign_in(self,client_name, client_ip, client_port):
        """
        For signing back in ater dereg.
        """
        self.client_table[client_name]["status"] = True # resets status to online
        print(self.client_table)
        client_message = {"message":self.client_table}
        broadcast_message = {"message":self.client_table}
        broadcast_packet = self.make_packet(broadcast_message) 
        client_packet = self.make_packet(client_message)
        
        self.broadcast(broadcast_packet, set(self.client_table.keys())) # updates all clients with table
        # return client_packet

    def register(self, client_name, client_ip, client_port):
        """
        for initial registration
        """
        self.client_table[client_name] = {"IP":client_ip, "port":client_port, "status":True}
        file = open("{}_saved.txt".format(client_name), "w") # creates blank txt file for savign offline messages
        file.close() 
        client_message = {"message":self.client_table}
        broadcast_message = {"message":self.client_table}
        broadcast_packet = self.make_packet(broadcast_message)
        client_packet = self.make_packet(client_message)
        self.broadcast(broadcast_packet, set(self.client_table.keys())) # updates all clients with table
        # return client_packet

    def degregister(self, client_name, client_ip, client_port):
        self.client_table[client_name]["status"] = False # sets status to offline
        client_message = {"message":self.client_table}
        broadcast_message = {"message":self.client_table}
        broadcast_packet = self.make_packet(broadcast_message)
        client_packet = self.make_packet(client_message)
        self.serverSocket.sendto(client_packet, (client_ip, client_port) )
        self.broadcast(broadcast_packet, set(self.client_table.keys()))
        # return client_packet
        
    def save_message(self, client, to, message):
        """
        appends offline messages to txt file in order they come in with datetime stamps
        """
        msg_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file = open("{}_saved.txt".format(to), "a")
        file.write(">>> {f}: <{d}> {m}".format(f =client, d = str(msg_date), m=message))
        file.write("\n")
        file = open("{}_saved.txt".format(to), "r")
        # print("MESSAGE SAVED FOR :", to)
        file.close()
    
    def get_save(self, client_name, client_ip, client_port ):
        file = open("{}_saved.txt".format(client_name), "r")
        messages = file.read()
        # print("GETTING MESSAGES :", client_name)
        # print(messages)
        # add server's message to client
        if messages =="": # if no messages
            messages = "[No new messages]\n"
        else:
            messages = "[You have messages]\n"+messages 
        file= open("{}_saved.txt".format(client_name), "w") # wipes the txt file clean so no old messages get resent
        self.serverSocket.sendto(self.make_packet({"message":messages}), (client_ip,client_port))
        # return 

    def send_ack(self, client_ip, client_port):
        ack = self.make_packet({"message":"ACK"})
        self.serverSocket.sendto(ack, (client_ip, client_port))

    def handle_request(self, packet, client_ip , client_port):
        """
        handles specific requests from clients
        [REQUEST:REG] + A = registration request from client A
        [REQUEST:DEREG] + A = deregistration request from client A
        [REQUEST:SAVE] + A + B + M = save offline message from client A to client B
        [REQUEST:GETSAVE] + A = get offline messages meant for client A 
        """
        # return ACK
        self.send_ack(client_ip, client_port)
        message = self.unpack_packet(packet)
        split_message = message["message"].split(" ")
        if split_message[0] == "[REQUEST:REG]" and len(split_message) == 2:
            # REG COMMAND FOUND and followed by second command (name) 
            # print("Registration requested for {}.".format(split_message[1]))
            if self.is_existing_client(split_message[1], client_ip, client_port):
                # CLIENT NAME EXISTS
                # DUPLICATE
                if self.duplicate: # if the name is a duplicate, reset the variable and tell client to come up with new name
                    self.duplicate = False
                    duplicate_response = {"message": "Username {} already in use. Duplicates will not be registered... ".format(split_message[1])}
                    return self.make_packet(duplicate_response) 
                # NOT DUPLICATE
                print("Client {} previously registered. Signing in...".format(split_message[1]))
                return self.sign_in(split_message[1], client_ip, client_port)
            else:
                # DOESN'T EXIST
                print("Client {} not previously registered. Now registering...".format(split_message[1]))
                return self.register(split_message[1], client_ip, client_port) 
        elif split_message[0] == "[REQUEST:DEREG]" and len(split_message) == 2:
            return self.degregister(split_message[1], client_ip, client_port)
        elif split_message[0] == "[REQUEST:GETSAVE]" and len(split_message) == 2:
            return self.get_save(split_message[1], client_ip, client_port)
        else:
            if split_message[0] == "[REQUEST:SAVE]" and len(split_message) >= 4:
                self.save_message(split_message[1], split_message[2], " ".join(split_message[3:]))
            return self.make_packet(message)

    def listen(self):
        print("Server listening...")
        while True:
            try:
                packet, clientAddress = self.serverSocket.recvfrom(4096) 
                client_ip, client_port = clientAddress
                # parse through message and send response
                self.handle_request(packet, client_ip, client_port)
                # self.serverSocket.sendto(response_message, clientAddress)
            except KeyboardInterrupt:
                print(">>> ctrl+c")
                self.serverSocket.close()

def main():
    args = sys.argv[1:]
    if args[0]=="-c" :
        if len(args)>5:
            print("Error in format:  too many parameters")
        if len(args)<5:
            print("Error in format:  too few parameters")
        client_name = args[1]
        server_ip = args[2]
        server_port = args[3]
        client_port = args[4]
        print("CLIENT MODE")
        client = Client(client_name, server_ip, server_port, client_port)
        
        client.run()
        
    elif args[0]=="-s" and len(args)==2:
        listening_port = int(args[1])
        if listening_port >= 1024 and listening_port<=65535:
            print("SERVER MODE")
            server = Server(listening_port)
            server.listen()
        else:
            print("Error in format: port must be between 1024 and 65535")
if __name__=="__main__":
    main()
    