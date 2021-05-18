'''
This module defines the behaviour of a client in your Chat Application
'''
import sys
import getopt
import socket
import random
from threading import Thread
import os
import queue
import util



'''
Write your code inside this class. 
In the start() function, you will read user-input and act accordingly.
receive_handler() function is running another thread and you have to listen 
for incoming messages in this function.
'''

ackCheck = False
seqNumCheck = 0

class Client:
    '''
    This is the main Client Class. 
    '''
    def __init__(self, username, dest, port, window_size):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username
        self.window = window_size
        
        #general purpose sender function to divide message into chunks , decide sequence numbers, handle acks 
    def sender(self,msgType,msgFormat,passMsg = None):
        
        
        global ackCheck
        global seqNumCheck
        
        SendToServerMessage = util.make_message(msgType,msgFormat,passMsg)
        stsMsgChunks = [SendToServerMessage[i:i+util.CHUNK_SIZE] for i in range(0, len(SendToServerMessage), util.CHUNK_SIZE)]
        seqNum = random.randint(1,100)
        clientStartPacket = util.make_packet("start",seqNum,)
        self.sock.sendto(clientStartPacket.encode("utf-8"), (self.server_addr, self.server_port)) #start packet sent
        
    
        for i in stsMsgChunks:
             
            if ackCheck == False:
                
                  while True:
                      
                      
                    
                    if ackCheck == True:
                        
                        break
            
            
            SendToServerPacket = util.make_packet("data", seqNumCheck, i)
            self.sock.sendto(SendToServerPacket.encode("utf-8"), (self.server_addr, self.server_port))
        
            ackCheck = False 
            
        seqNumCheck = seqNumCheck + 1
        endPacket = util.make_packet("end", seqNumCheck,)
        self.sock.sendto(endPacket.encode("utf-8"), (self.server_addr, self.server_port))
        
            
                    #1 make message 
                    #2 convert to chunks
                    #3 send start packet, gen random int
                    #4 traverse list of chunks,check when ACKcheck == true, send chunks. set ackcheck to false
                    #5 send end packet.
                    
        
    def start(self):
        
        global ackCheck
        quitCheckA = True
        
        
        self.sender("join",1,self.name)
        
        while quitCheckA:
            

            SendToServerMessage = input()
            inputList = SendToServerMessage.split()
            
            if SendToServerMessage == "list":
                self.sender("request_users_list",2,)
                
                
            elif SendToServerMessage[:3] == "msg":
                self.sender("send_message",4," ".join(inputList)) 
                
                
            elif SendToServerMessage[:4] == "file":
                
                fileName = inputList[-1] #filename stored
                filePtr = open(fileName,'r') #opens and starts reading file
                fileData = filePtr.read() #file content
                fileReceiverData = inputList[0:-1]
                fileContent = []
                fileContent.append(" ".join(fileReceiverData))
                fileContent.append(self.name)
                fileContent.append(str(fileName))
                fileContent.append(fileData)
                
                self.sender("send_file",4," ".join(fileContent)) 
                
            
            elif SendToServerMessage == "quit":
                print("quitting")
                self.sender("disconnect",1,self.name)
                quitCheckA = False
                break
            
            elif SendToServerMessage == "help":
                print("FORMATS:")
                print("Message: msg <number_of_users> <username1> <username2> … <message>")
                print("Available Users: list")
                print("File Sharing: file <number_of_users> <username1> <username2> … <file_name>")
                print("Quit: quit")
                
            else:
                print("incorrect userinput format")
                    
        # raise NotImplementedError
            

    def receive_handler(self):
        global ackCheck
        global seqNumCheck
        
        quitCheck = True
        
        q2 = queue.Queue()
        
        while quitCheck:
            
            msg = ""
            serverPacket,_ = self.sock.recvfrom(self.server_port)
            serverPacketDecoded = serverPacket.decode("utf-8")
            serverConnectionMessage, recSeqNum, serverMessage, _, = util.parse_packet(serverPacketDecoded)
            
            
            
            # clientAckPacket = util.make_packet("ack", intSeqNum,)
            # self.sock.sendto(serverAckPacket.encode("utf-8"),clientAddress)
            
            serverMsg = serverMessage.split()
            
            
            if serverConnectionMessage == "ack":
                recSeqNumber = int(recSeqNum)
                seqNumCheck = recSeqNumber
                ackCheck = True
                    
            elif serverConnectionMessage == "start":
                
                recSeqNumber = int(recSeqNum)
                seqNumCheck = recSeqNumber
                clientAckPacket = util.make_packet("ack", recSeqNumber,)
                self.sock.sendto(clientAckPacket.encode("utf-8"),(self.server_addr,self.server_port))
                
            elif serverConnectionMessage == "data":
                q2.put(serverMessage)
                
                recSeqNumber = int(recSeqNum)
                seqNumCheck = recSeqNumber
                clientAckPacket = util.make_packet("ack", recSeqNumber,)
                self.sock.sendto(clientAckPacket.encode("utf-8"),(self.server_addr,self.server_port))
                
            elif serverConnectionMessage == "end":
                
                while not q2.empty():
                    msg += q2.get()

                serverMsg = msg.split()    
                
                print(serverMsg)
                
                if(serverMsg[0] == "response_users_list"):
                    ackCheck = True
                    print("list:"," ".join(serverMsg[2:]))
                    
                elif(serverMsg[0] == "msg:"):
                    print(" ".join(serverMsg))
                
                elif(serverMsg[0] == "forward_message"):
                    
                    userCounter = int(serverMsg[5])
                    actualMessage = serverMsg[6+userCounter:-1]
                    senderName = str(serverMsg[-1])
                    
                    print("msg:","".join(senderName+":")," ".join(actualMessage))
                
                elif(serverMsg[0] == "forward_file"):
                    
                    newUserCounter = int(serverMsg[5])
                    newFileName = str(self.name)+"_"+str(serverMsg[5+newUserCounter+2])
                    newSenderName = str(serverMsg[6+newUserCounter])
                    newFilePtr = open(newFileName,'w')
                    newFilePtr.write(" ".join(serverMsg[5+newUserCounter+3:]))
                    newFilePtr.close()
                    print("file:","".join(newSenderName+":"),str(serverMsg[5+newUserCounter+2]))
                    
                elif(serverMsg[0] == "err_unknown_message"):
                    
                    print("disconnected: server received an unknown command")
                    quitCheck = False
                    break
                    
                    # quitMessage = util.make_message("disconnect",1,self.name)
                    # quitMessagePacket = util.make_packet(msg=quitMessage)
                    # self.sock.sendto(quitMessagePacket.encode("utf-8"),(self.server_addr,self.server_port))
                    # self.sock.close()
                    # break
                
                elif(serverMsg[0] == "err_server_full"):
                    print("disconnected: server full")
                    quitCheck = False
                    break
                    # quitMessage = util.make_message("disconnect",1,self.name)
                    # quitMessagePacket = util.make_packet(msg=quitMessage)
                    # self.sock.sendto(quitMessagePacket.encode("utf-8"),(self.server_addr,self.server_port))
                    # self.sock.close()
                    # break
                
                elif(serverMsg[0] == "err_username_unavailable"):
                    print("disconnected: username not available")
                    quitCheck = False
                    break
                    # quitMessage = util.make_message("disconnect",1,self.name)
                    # quitMessagePacket = util.make_packet(msg=quitMessage)
                    # self.sock.sendto(quitMessagePacket.encode("utf-8"),(self.server_addr,self.server_port))
                    # self.sock.close()
                    # break
                    
            continue
        # raise NotImplementedError



# Do not change this part of code
if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our Client module completion
        '''
        print("Client")
        print("-u username | --user=username The username of Client")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW_SIZE | --window=WINDOW_SIZE The window_size, defaults to 3")
        print("-h | --help Print this help")
    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "u:p:a:w", ["user=", "port=", "address=","window="])
    except getopt.error:
        helper()
        exit(1)

    PORT = 15000
    DEST = "localhost"
    USER_NAME = None
    WINDOW_SIZE = 3
    for o, a in OPTS:
        if o in ("-u", "--user="):
            USER_NAME = a
        elif o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW_SIZE = a

    if USER_NAME is None:
        print("Missing Username.")
        helper()
        exit(1)

    S = Client(USER_NAME, DEST, PORT, WINDOW_SIZE)
    try:
        # Start receiving Messages
        T = Thread(target=S.receive_handler)
        T.daemon = True
        T.start()
        # Start Client
        S.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
