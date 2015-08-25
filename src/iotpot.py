#! /usr/bin/python
# -*- coding: utf-8 -*-
# last modified : 2015/08/24

import SocketServer
import sys
import socket
import datetime
import time
import subprocess
import threading

TIMEOUT = 300
PROMPT = "~ $ "
BUXYBOX = "\x0d\x0a\x0d\x0a\x0d\x0aBusyBox v1.1.2 (2007.05.09-01:19+0000) Built-in shell (ash)\x0d\x0a" \
          "Enter 'help' for a list of built-in commands.\x0d\x0a\x0d\x0a"
QEMUPASS = "iotpot"

# known command dictionary
cmd_dict = {}
cmd_dict["test\x0d\x0a"] = "test\x0d\x0a"

class FrontEndResponder(SocketServer.StreamRequestHandler):
# The Handler class as frontend responder

    def __init__(self,request,client_address,server):
        self.attackerIP = ""
        self.PORTNUMBER = ""
        self.payload = ""
        self.date = datetime.datetime.today()
        self.proxySocket = None
        SocketServer.StreamRequestHandler.__init__(self,request,client_address,server)

    def handle(self):
        self.receiveQueue = []
        self.attackerIP = self.client_address[0]
        self.PORTNUMBER = self.server.server_address[1]
        self.request.setblocking(0)
        print "%s IP %s.%s > %s.%s : try to connect" \
            % (self.date,self.attackerIP,self.client_address[1],\
               self.server.server_address[0],self.PORTNUMBER)
        th = BackEndResponder(self.attackerIP,self.PORTNUMBER,self.request,self.receiveQueue)
        th.start()
        success_list = []
        with open("../etc/accept_userpass", 'r') as fp:
            for line in fp:
                pass_list.append(line.strip()+"\x0d\x0a")

        # main roop of FrontEndResponder
        while True:
            if (datetime.datetime.today() - self.date).seconds > TIMEOUT:
                break

            # receive response from Attacer
            try:
                self.payload = self.request.recv(8192)
                if len(self.payload) != 0:
                    if (self.payload in pass_list) == True:
                        self.payload =  QEMUPASS+"\x0d\x0a"

                    # known command
                    if cmd_dict.has_key(self.payload) == True:
                        self.payload = cmd_dict.get(self.payload,"NOT FOUND")+PROMPT
                        self.request.send(self.payload)

                    # unknown command
                    else:
                        self.receiveQueue.append(self.payload)

            except socket.error:
                pass

            # check reveice Queue
            if len(th.receiveQueue) != 0:
                sendData = th.receiveQueue.pop(0)
                self.request.send(sendData)
                self.date = datetime.datetime.today()

        self.request.close()
        print "%s IP %s.%s > %s.%s : session closed" \
            % (self.date,self.attackerIP,self.client_address[1],self.server.server_address[0],self.PORTNUMBER)


class BackEndResponder(threading.Thread):
# The Thread class as backend responder

    def __init__(self,qemuIP,PORTNUMBER,proxyThreadRequest,proxyThreadQueue):
        self.proxyThreadQueue = proxyThreadQueue
        self.receiveQueue = []
        self.proxyThreadRequest = proxyThreadRequest
        self.qemuIP = sys.argv[2]
        self.PORTNUMBER = PORTNUMBER
        self.responce = ""
        self.date = datetime.datetime.today()
        self.qemuSocket = None
        threading.Thread.__init__(self)

        if not self.qemuSocket:
          self.qemuSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
          try:
            self.qemuSocket.connect((self.qemuIP,int(self.PORTNUMBER)))
          except IndexError:
            print "Error Connection to Qemu"

    def run(self):
        self.qemuSocket.setblocking(0)
        while True:
            if ( datetime.datetime.today() - self.date).seconds > TIMEOUT:
                break

            try:
                # receive responce from Qemu
                self.responce = self.qemuSocket.recv(8192)
                if len(self.responce) != 0:
                    self.receiveQueue.append(self.responce)
            except:
                pass

            # check receive Queue
            if len(self.proxyThreadQueue) != 0:
                sendData = self.proxyThreadQueue.pop(0)
                self.qemuSocket.send(sendData)
                self.date = datetime.datetime.today()

        print "%s : BackEndResponder session closed" % self.date

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage: python %s QemuIPaddr " % sys.argv[0],sys.exit(-1)

    PORT = int(sys.argv[1])
    server = SocketServer.ThreadingTCPServer(('', 23), FrontEndResponder)
    print "=== Set up IoTPOT ==="
    server.serve_forever()
