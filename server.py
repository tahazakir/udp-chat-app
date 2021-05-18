'''
This module defines the behaviour of server in your Chat Application
'''
import sys
import getopt
import socket
import random
from threading import Thread
import util
import queue

#checks to see if ack has been received
ackChecker = False
#for storing clients
q1 = queue.Queue()

clientList = []
clients = []
clientAddresses = {} #make a dictionary, key hogi client ka addr aur uskay against name store hojaye ga

class Server:
    '''
    This is the main Server Class. You will to write Server code inside this class.
    '''
    
    
    def __init__(self, dest, port, window):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind((self.server_addr, self.server_port))
        self.window = window
        
        
    
        
    #general purpose sender function to divide message into chunks , decide sequence numbers, handle acks 
    def sender(self,msgType,msgFormat, clientAddr, passMsg = None):
        
        
        global ackChecker
        global q1
        global clients
        global clientAddresses
        
        
        SendToClientMessage = util.make_message(msgType,msgFormat,passMsg)
        stsMsgChunks = [SendToClientMessage[i:i+util.CHUNK_SIZE] for i in range(0, len(SendToClientMessage), util.CHUNK_SIZE)]
        seqNumber = random.randint(1,100)
        clientStartPacket = util.make_packet("start",seqNumber,)
        self.sock.sendto(clientStartPacket.encode("utf-8"),clientAddr) #start packet sent

        
        for i in stsMsgChunks:
             
            
            if ackChecker == False:
                
                  while True:
                    
                    if ackChecker == True:
                        
                        break
            
            
            SendToServerPacket = util.make_packet("data", seqNumber, i)
            self.sock.sendto(SendToServerPacket.encode("utf-8"),clientAddr)
            ackChecker = False 
            
        
        endPacket = util.make_packet("end",seqNumber,)
        self.sock.sendto(endPacket.encode("utf-8"), clientAddr)
        
    
    #general purpose process ftn that deals with all the individual functionalities of action availaible to the client
    def process(self, clientAddress):
                
        global q1
        global clients
        global clientAddresses
        global clientList
        
        packetCombiner = []
        
        for i in clientList:
                if i[1] == clientAddress:
                    clientQ = i[0]

                    
        cPack = clientQ.get()
        
        
        clientPacketDecoded = cPack.decode("utf-8")
        connectionMessage, sequenceNum, clientMessage , _ = util.parse_packet(clientPacketDecoded)

        while connectionMessage != "end":
            packetCombiner.append(clientMessage)
            cPack = clientQ.get()
            clientPacketDecoded = cPack.decode("utf-8")
            connectionMessage, sequenceNum, clientMessage , _ = util.parse_packet(clientPacketDecoded)
            
        
        cMsg = ""
        
        for i in packetCombiner:
            cMsg += i
            
        name = cMsg.split()
        clientKeyList = list(clientAddresses.keys())
        clientValueList = list(clientAddresses.values())
        
        if name != []:
                
            if name[0] == "join": 
                if name[2] in clients:
                    self.sender("err_username_unavailable",2,clientAddress,)
                    print("disconnected: username not available")

                elif len(clients) >= util.MAX_NUM_CLIENTS:
                    self.sender("err_server_full",2,clientAddress,)
                    print("disconnected: server full")
                    
                
                else:
                    clients.append(name[2])
                    clientAddresses[clientAddress] = name[2]
                    print("join:",name[2])
            
            elif name[0] == "request_users_list":
                clients.sort()
                listNames = " "
                listNames = " ".join(clients)
                self.sender("response_users_list",3,clientAddress,listNames)
                print("request_users_list:",clientAddresses[clientAddress])
            
            elif name[0] == "send_message":
                
                if not name[3].isdigit(): 
                    
                    self.sender("err_unknown_message",2,clientAddress,)
                    print("disconnected:",clientAddresses[clientAddress],"sent unknown command")
                    clients.remove(str(clientAddresses[clientAddress]))
                    del clientAddresses[clientAddress]
                    
                    
                
                else:
                    
                    
                    receivingUserCount = int(name[3])
                    receivingUserNames = name[4:4+receivingUserCount]
                    
                    print("msg:",clientAddresses[clientAddress])
                    
                    
                    name.append(clientAddresses[clientAddress])
                    
                    for i in receivingUserNames:
                        if i in clients:
                            
                            
                            receiverAddress = clientKeyList[clientValueList.index(i)]
                            self.sender("forward_message",4,receiverAddress," ".join(name))
                            
                        
                        else:
                            print("msg:",clientAddresses[clientAddress],"to non-existent user",i)

            elif name[0] == "send_file":

                if not name[3].isdigit():
                    
                    self.sender("err_unknown_message",2,clientAddress,)
                    print("disconnected:",clientAddresses[clientAddress],"sent unknown command") 
                    clients.remove(str(clientAddresses[clientAddress]))
                    del clientAddresses[clientAddress]
                    
                    
                
                else:
                    receivingUserCount = int(name[3])
                    receivingUserNames = name[4:4+receivingUserCount]
                    print("file:",clientAddresses[clientAddress])
                    
                    for i in receivingUserNames:
                        if i in clients:
                    
                            fileReceiverAddress = clientKeyList[clientValueList.index(i)]
                            self.sender("forward_file",4,fileReceiverAddress,cMsg)
                            
                            
                        else:
                            print("file:",clientAddresses[clientAddress],"to non-existent user",i)
                
            elif name[0] == "disconnect":
            
                clients.remove(str(name[2]))
                print("disconnected:",name[2])
    
    def start(self):
        
        global q1
        global ackChecker
        global clients
        global clientAddresses
        # clients = []
        # packetCombiner = []
        # clientAddresses = {} #make a dictionary, key hogi client ka addr aur uskay against name store hojaye ga
        
        while True:
            clientPacket, clientAddress = self.sock.recvfrom(4096)
            clientInfo = (clientPacket, clientAddress)
            q1.put(clientInfo)
            
            clientPacketDecoded = clientPacket.decode("utf-8")
            connectionMessage, sequenceNum, clientMessage , _ = util.parse_packet(clientPacketDecoded)
            intSeqNum = int(sequenceNum)
            intSeqNum = intSeqNum + 1
            
            if connectionMessage == "start": #threads on basis of start packet
                #create thread for process ftn
                T = Thread(target=self.process, args=(clientAddress,))
                clientList.append((queue.Queue(),clientAddress))                
                T.start()
                
            if connectionMessage == "data":
                for i in clientList:
                    if i[1] == clientAddress:
                        i[0].put(clientPacket)
                        
            if connectionMessage == "end":
                for i in clientList:
                    if i[1] == clientAddress:
                        i[0].put(clientPacket)
                        
            if connectionMessage == "ack":
                ackChecker = True
                
                        
            serverAckPacket = util.make_packet("ack", intSeqNum,)
            self.sock.sendto(serverAckPacket.encode("utf-8"),clientAddress) #acks sent
                        
                
        # raise NotImplementedError

# Do not change this part of code

if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our module completion
        '''
        print("Server")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW | --window=WINDOW The window size, default is 3")
        print("-h | --help Print this help")

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "p:a:w", ["port=", "address=","window="])
    except getopt.GetoptError:
        helper()
        exit()

    PORT = 15000
    DEST = "localhost"
    WINDOW = 3

    for o, a in OPTS:
        if o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW = a

    SERVER = Server(DEST, PORT,WINDOW)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
