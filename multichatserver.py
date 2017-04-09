import sys
import socket
import select
import pyaudio
import wave
import time

from threading import Thread
from SocketServer import ThreadingMixIn

#Default variable definitions---------------------------------------------------------------------------------------------------------------------------------------------------------------------
SOCKET_LIST=[0]
SOCKET_IP={}
SOCKET_PORT={}
IP_DATA={}
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

######################################################################################Thread##########################################################################################################
#File Handling-----------------------------------------------------
class Nthread(Thread):
	def __init__(self,clientsocketrecv,clientsocketsend):
		Thread.__init__(self)
		self.sockrecv=clientsocketrecv
		self.socksend=clientsocketsend
	def run(self):
		filename=self.sockrecv.recv(1024)
		print "File :",filename		
		self.sockrecv.send("done")
		
		self.socksend.send(filename)
		self.socksend.recv(4)
		#print "Inside thread"
		#Recieving and sending data
		while True:
			data = self.sockrecv.recv(1024)
			self.socksend.send(data)
			if not data:
				break
			
		print "\nFile Recieved and Sent"
		self.sockrecv.close()
		self.socksend.close()
#-------------------------------------------------------------------
#TCP Bandwidth------------------------------------------------------
class tcpbw(Thread):
	def __init__(self,tcpclientsock):
		Thread.__init__(self)
		self.tcpclientsock=tcpclientsock
	def run(self):
		i=0
		while True:
			data = self.tcpclientsock.recv(1024)
			#print data
			i=i+1
			if not data:
				break
			del data
		#print "success"
		i=str(i)
		self.tcpclientsock.send(i)	
		self.tcpclientsock.close()
#---------------------------------------------------------------------

###################################################################################################################################################################################################

############################################################################Basic Operation######################################################################################################## 

#Chatting options---------------------------------------------------------
#Broadcastmessage to all Clients
def sendall(serversocket,clientsocket,message):
	for sock in SOCKET_LIST[1:]:
		if sock != serversocket and sock != clientsocket:
			try:
				sock.send(message)
			except:
				sock.close()
				SOCK_LIST.remove(sock)
				SOCKET_IP.pop(sock)
				SOCKET_PORT.pop(sock)
#Sending to the single client						
def senddata(ip,message):
	#print "Single"
	#print SOCKET_IP.items()
	a=0
	for sock,i in SOCKET_IP.items():
		if i == ip:
			a=1
			sock.send(message) 
		if a==0:
			a=0
			IP_DATA[ip]=message
def voipdata(message,reqsock,ip):
	REQ_LIST=[reqsock]
	if message == "voip":	
		for sock,i in SOCKET_IP.items():
			if i == ip:
				print "Requesting server to start"
				sock.send("VOIP-request")
			else :
				reqsock.send("Client Not active")	
	elif message == "readytorecieve":
		print "Requesting client to start"
		REQ_LIST[0].send("startvoip")
		REQ_LIST=[]
#Buffering message in case not active
def previousmessage(ip):
	for i,msg in IP_DATA.items():
		if i == ip:
			data = msg
			senddata(ip,msg)
			IP_DATA.pop(ip)
	
#Sending List of Clients connected to the server
def listcall(clientsocket):
	clientsocket.send("\nLIST")
	for sock in SOCKET_LIST[2:]:
		IP=SOCKET_IP[sock]
		PORT=SOCKET_PORT[sock]
		HOSTNAME=socket.gethostbyaddr(IP)
		message="[%s:%s:%s]"%(IP,PORT,HOSTNAME[0])
		#print "Message: ",message
		try:
			clientsocket.send(message) 
		except:
			sock.close()
			SOCK_LIST.remove(socket)
			SOCKET_IP.pop(sock)
			SOCKET_PORT.pop(sock)
	clientsocket.send("\nLIST END")
#-----------------------------------------------------------------------------

#File Activities--------------------------------------------------------------
#Creating sockets to communicate with clients to transfer a file
def recievefilesocket(destsock):
	#Creating sockets
	filerecvsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	host=socket.gethostname()
	filerecvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	filerecvsock.bind(("",5001))
	filerecvsock.listen(5)
	#Creating sockets
	destsock.send("recievefile")
	filesendsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	host=socket.gethostname()
	filesendsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	filesendsock.bind(("",5002))
	filesendsock.listen(5)
	
	#Accept Connections
	(clientsocketrecv,(ip1,port1))=filerecvsock.accept()
	#print "Recieving file from",(ip1,port1)
	#print "Sending"

	(clientsocketsend,(ip2,port2))=filesendsock.accept()
	#print "Sending file to",(ip2,port2)
	#print "Sending"		
	#Creating a thread
	thread=Nthread(clientsocketrecv,clientsocketsend)
	#Starting a thread
	thread.start()
#--------------------------------------------------------------------------------

#TCP Bandwidth Activities -------------------------------------------------------
def tcpbandwidth(sock):
	print "tcp"
	#Creating sockets
	tcprecvsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	host=socket.gethostname()
	tcprecvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	tcprecvsock.bind(("",5003))
	tcprecvsock.listen(2)
	sock.send("tcp")
	print "tcp1"
	#Accept Connections
	(tcpclientsock,(ip1,port1))=tcprecvsock.accept()
	print "tcp2"
	#Creating a thread
	thread=tcpbw(tcpclientsock)
	#Starting a thread
	thread.start()
#--------------------------------------------------------------------------------
#Dispalying List-----------------------------------------------------------------
#Displaying the list connected to server
def listdisplay():
	print "\nList"
	for sock in SOCKET_LIST[2:]:
		#print "list"
		IP=SOCKET_IP[sock]
		PORT=SOCKET_PORT[sock]
		HOSTNAME=socket.gethostbyaddr(IP)
		message="[%s:%s:%s]\n"%(IP,PORT,HOSTNAME[0])
		print "\n",message
	print "\nList End"
#--------------------------------------------------------------------------------
#Simple data handling------------------------------------------------------------
#Parsing Data to identify command from client
def dataparser(data):
	job=data.split()
	return job[0]
#Parsing data to identify destination IP addressOCKET
def ipparser(data):
	job=data.split()
	#print job[1]	
	return job[1]
def sockfinder(ip):
	print SOCKET_IP
	for sock,i in SOCKET_IP.items():
		print sock,i
		if i == ip:
			return sock
		
	return 0
#---------------------------------------------------------------------------------
############################################################################################################################################################################################################
port = sys.argv[1]
port = int(port)

#Basic socket intialization------------------------------------------------------------------------------------------------------------------------------------------
#Creating sockets
serversocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#hostname
host=socket.gethostname()
#print host
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#binding socket and address
serversocket.bind(("",port))
serversocket.listen(5)
SOCKET_LIST.append(serversocket)

while 1:
	#Use select function to check all the sockets in the list
	#ready_to_read, ready_to_write, in_error = \select.select(potential_readers,potential_writers,potential_errs,timeout)
	ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
	for sock in ready_to_read:
		#Input from User
		if sock == 0:
			command=raw_input()
			command.lower()
			if command == "list":
				#Displaying List of clients connected					
				print "\nLIST"
				listdisplay()
				print "\nLIST END"
			if command == "exit":
				sys.exit()	
		#Accepting new Connections to the Server			
		elif sock == serversocket:
			#Connection to client
			#Server accepting new connection
			(clientsocket,addr)=serversocket.accept()
			(ip,port)=addr
			print "\nConnection from",(ip,port)
			SOCKET_LIST.append(clientsocket)
			SOCKET_IP[clientsocket]=ip
			SOCKET_PORT[clientsocket]=port
			listcall(clientsocket)
			previousmessage(ip)	
			sendall(serversocket,clientsocket,"\n[%s:%s]New Client added"%(ip,port))
		#Data recived from client		
		else :
			try:
				#Recieving data from the client				
				data=sock.recv(1024)
				print "\nData on ",str(sock.getpeername())
				print data
				if data:
					job=dataparser(data)
					job=job.lower()
					#Forwarding data to all
					if job == "broadcast":
						l=len(job)+1
						sendall(serversocket,sock,"[" + str(sock.getpeername()) + "] " + data[l:])
					#Sending List to all Client					
					elif job == "list":
						listcall(sock)
					#Sending List to single requested Client
					elif job == "send":
						ip=ipparser(data)
						l=len(job)+2+len(ip)
						senddata(ip,data[l:])
					#Voip connection
					elif job == "voip":
						ip=ipparser(data)
						voipdata("voip",sock,ip)
					elif job == "readytorecieve":
						voipdata("readytorecieve",sock,"0")
					#Request for uploading a file
					elif job == "put":
						#print "File Handling"
						ip=ipparser(data)
						destsock=sockfinder(ip)
						if destsock == 0:
							sock.send("Client not active or wrong address")
						else:
							sock.send("sendfile")
							#destsock.send("recievefile")						
							recievefilesocket(destsock)
					#Request for downloading a file
					elif job == "get":
						ip=ipparser(data)
						destsock=sockfinder(ip)
						if destsock == 0:
							sock.send("Source not active or wrong address")
						else:
							name=data.split()
							filename=name[2]
							message = "filerequest "+filename
							print message
							destsock.send(message)
							recievefilesocket(sock)
					#Requesting Bandwidth 
					elif job == "tcp":
						#print "TCP"
						tcpbandwidth(sock)
						
				#REmoving client from the list in case no data recieved
				else:
					if sock in SOCKET_LIST:
						SOCKET_LIST.remove(sock)
						SOCKET_IP.pop(sock)
						SOCKET_PORT.pop(sock)
						sendall(serversocket,clientsocket,"\n[%s:%s] Client offline"%addr)
			#Removing client from the list			
			except:
				sendall(serversocket,sock,"\n[%s:%s] Client offline"%addr)			
