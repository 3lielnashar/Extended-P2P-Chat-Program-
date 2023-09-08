
from socket import *
import sys
import threading
import time
import select
import logging


# Room Client side of peer
class RoomPeerClient(threading.Thread):
    # variable initializations for the client side of the peer
    def __init__(self, servers, username, peerServer, room_id, registry_connection, responseReceived=None):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.servers = servers
        # keeps the username of the peer
        self.username = username
        # client side tcp socket initialization
        self.tcpClientSockets = {}
        # keeps the room name of the peer
        self.roomId = room_id

        self.registry_connection = registry_connection
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived
        # keeps if this client is ending the chat or not
        self.isEndingChat = False

    def createClientSockets(self, servers):
        connections = {}
        for name, server in servers.items():
            connections[name] = socket(AF_INET, SOCK_STREAM)
            try:
                connections[name].connect(server)
                connections[name].setblocking(0)
            except ConnectionRefusedError as crErr:
                logging.error("ConnectionRefusedError: {0}".format(crErr))
                del connections[name]

        return connections
    
    def sendMessageToAll(self, message):
        for name, socket in self.tcpClientSockets.items():
            #print("Sending message to " + name)
            socket.send(message)

    def closeAllSockets(self):
        for name, socket in self.tcpClientSockets.items():
            socket.close()
    
    def getServersinRoom(self):
        message = f"LIST-ROOM {self.roomId} {self.peerServer.peerServerPort}"
        self.registry_connection.send(message.encode())
        response = self.registry_connection.recv(1024).decode()
        
        roomServers = response.split()[2:]
        servers = {}
        for server in roomServers:
            serverList = server.split(',')
            if len(serverList) > 1:
                #print(serverList)
                if serverList[0] != self.username:
                    servers[serverList[0]] = (serverList[1], int(serverList[2]))
        return servers

    def updateConnections(self):
        #print("Updating connections...")
        currentServers = self.getServersinRoom()
        #print(currentServers)
        clientsToRemove = []
        for name, socketConnection in self.tcpClientSockets.items():
            
            if name not in currentServers:
                socketConnection.close()
                clientsToRemove.append(name)
            else:
                currentServers.pop(name)

        for clientToRemove in clientsToRemove:
            del self.tcpClientSockets[clientToRemove]
        #print("Clients to remove: ", clientsToRemove)

        for name, server in currentServers.items():
            #print(name, server)
            self.tcpClientSockets[name] = (socket(AF_INET, SOCK_STREAM))
            try:
                self.tcpClientSockets[name].connect(server)
                self.tcpClientSockets[name].setblocking(0)
            except ConnectionRefusedError as crErr:
                logging.error("ConnectionRefusedError: {0}".format(crErr))
                del self.tcpClientSockets[name]

    def leaveRoom(self):
        message = f"LEAVE-ROOM {self.roomId}".encode()
        logging.info("Send to registry -> " + message.decode())
        self.registry_connection.send(message)
        response = self.registry_connection.recv(1024).decode()
        logging.info("Received from registry -> " + response)
        #print(response)

    # main method of the peer client thread
    def run(self):
        print("Peer client started...")
        print(f"Peer client is connecting to servers...")
        # connects to the server of other peer
        self.tcpClientSockets = self.createClientSockets(self.servers)
        self.peerServer.inRoom = True

        # as long as the server status is chatting, this client can send messages
        while True:
            # message input prompt
            messageSent = input(self.username + ": ")
            messageSent = f"ROOM-MESSAGE {self.username}: {messageSent}"
            # sends the message to the connected peer, and logs it
            self.updateConnections()
            self.sendMessageToAll(messageSent.encode())
            logging.info("Send to room -> " + messageSent)
            #print("Message sent to room")
            # if the quit message is sent, then the server status is changed to not chatting
            # and this is the side that is ending the chat
            if ":q" in messageSent:
                self.peerServer.isChatRequested = 0
                self.isEndingChat = True
                self.peerServer.inRoom = False

                self.leaveRoom()
                # closes the socket
                self.responseReceived = None
                self.closeAllSockets()
                break
            
                