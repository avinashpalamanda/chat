import socket
import time
import os
import sys
import socket
import select
import pyaudio
import wave
import time


from threading import Thread
from SocketServer import ThreadingMixIn

global filename
a=0
voipip=""
THREAD_LIST=[]
##############################################################################3Thread#############################################################################################################3
#File Handling threads------------------------------------------------
#Sending a file file
class Nthread(Thread):
	def __init__(self,sendsock):
		Thread.__init__(self)
		self.sock=sendsock
		
	def run(self):
		#Opening file and sending data
		#filename="test.txt"
		#print "send",filename
		
		self.sock.send(filename)
		self.sock.recv(4)
		f=open(filename,'rb')
		start=time.time()				
		for i in f:
			self.sock.send(i)
			#print "sent",repr(i)
		f.close()
		stop=time.time()
		os.system('clear')		
		print "\nFile sent, Duration :",stop-start
		self.sock.send("file-sent")
		self.sock.close()
		menu()
#Recieving a file
class Nthread1(Thread):
	def __init__(self,recvsock): 
		Thread.__init__(self)
		self.sock=recvsock
	def run(self):
		os.system('clear')
		filename=self.sock.recv(1024)
		print "recv",filename
		
		f=open("../recv/"+filename,'wb')
		self.sock.send("done")
		while True:
			data = self.sock.recv(1024)
			if not data:
				break
			f.write(data)
		f.close()
		print "\nFile Recieved"
		handle = open("recieveddata.txt",'wb')
		handle.write("File Recieved " + " ")
		self.sock.close()
		menu()
#-------------------------------------------------------------------------
#TCP Bandwidth -----------------------------------------------------------
class tcpbw(Thread):
	def __init__(self,sendsock):
		Thread.__init__(self)
		self.sock=sendsock
	def run(self):
		#Creating data and sending
		data = 'x' * (1023) + '\n'		
		start=time.time()
		try:
			self.sock.connect((host,5003))
		except:
			print "Unable to connect"
			sys.exit()
		i=0				
		while i < 1000:
			self.sock.send(data)
			#print "sent",i
			i=i+1
		self.sock.shutdown(1)
		data=self.sock.recv(1024)
		print data
		count = int(data)
		stop=time.time()	
		print "Duration",stop-start	
		print "Bandwidth :",round(1024*0.000001*8*(i-1))/(stop-start)
		handle = open("recieveddata.txt",'wb')
		handle.write("Bandwidth :" + str(round(1024*0.000001*8*(i-1))/(stop-start)))
		self.sock.close()
		menu

class voipstart(Thread):
	def __init__(self,sock,PORT):
		Thread.__init__(self)
		self.sock=sock
		self.PORT=PORT
	def run(self):
		print "voip client start"
		#record
		CHUNK = 1024
		FORMAT = pyaudio.paInt16
		CHANNELS = 1
		RATE = 44100
		RECORD_SECONDS = 40

		HOST = voipip    # The remote host
		#PORT = 6000              # The same port as used by the server

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((HOST, self.PORT))

		p = pyaudio.PyAudio()

		stream = p.open(format=FORMAT,
				channels=CHANNELS,
				rate=RATE,
				input=True,
				frames_per_buffer=CHUNK)

		print("*recording")
		
		frames = []

		for i in range(0, int(RATE/CHUNK*RECORD_SECONDS)):
			data  = stream.read(CHUNK)
			frames.append(data)
			s.sendall(data)

		print("*done recording")

		stream.stop_stream()
		stream.close()
		p.terminate()
		s.close()

		print("*closed")


class voiprecv(Thread):
	def __init__(self,sock,PORT):
		Thread.__init__(self)
		self.sock=sock
		self.PORT=PORT
	def run(self):
		print "voip server start"
		CHUNK = 1024
		FORMAT = pyaudio.paInt16
		CHANNELS = 1
		RATE = 44100
		RECORD_SECONDS = 4
		WAVE_OUTPUT_FILENAME = "server_output.wav"
		WIDTH = 2
		frames = []

		p = pyaudio.PyAudio()
		stream = p.open(format=p.get_format_from_width(WIDTH),
				channels=CHANNELS,
				rate=RATE,
				output=True,
				frames_per_buffer=CHUNK)


		HOST = ''                 # Symbolic name meaning all available interfaces
		#PORT = 6000              # Arbitrary non-privileged port
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((HOST, self.PORT))
		s.listen(1)
		self.sock.send("readytorecieve")
		conn, addr = s.accept()
		print ('Connected by', addr)
		data = conn.recv(1024)
		while data != '':
			stream.write(data)
			data = conn.recv(1024)
			frames.append(data)
			os.system('clear')
		wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
		wf.setnchannels(CHANNELS)
		wf.setsampwidth(p.get_sample_size(FORMAT))
		wf.setframerate(RATE)
		wf.writeframes(b''.join(frames))
		#wf.close()

		stream.stop_stream()
		stream.close()
		p.terminate()
		conn.close()
#---------------------------------------------------------------------------

#####################################################################################################################################################################################################

########################################################################Functions Used in the code##################################################################################################
#File-----------------------------------------------------------------------
#Function to send a file
def filesendsock():
	host=sys.argv[1]
	#host=socket.gethostname()
	port = 5001
	#Client socket
	sendsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sendsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	try:
		sendsock.connect((host,port))
		#print "Connecting to send"	
		threads=[]
		#Creating a thread
		thread=Nthread(sendsock)
		#Starting a thread
		thread.start()	
	except:
		print "Unable to connect"
		#sys.exit()

#Function to recieve a file
def filerecievesock():
	host=sys.argv[1]
	port = 5002
	#Client socket
	recvsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	recvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	try:
		recvsock.connect((host,5002))
		threads=[]
		#Creating a thread
		thread=Nthread1(recvsock)
		#Starting a thread
		thread.start()	
	except:
		print "Unable to connect"
		#sys.exit()

#File Handler
def filehandler(msg,clientsocket):
	filename=""
	l=msg.split()
	if len(l) == 1:
		msg=raw_input()
		l=msg.split()
		x=len(l)
		if x == 3:
			cmd=msg.split()
			if cmd[0] == "put":
				if os.path.isfile(cmd[2]):
					filename=cmd[2]
					clientsocket.send(msg)
				else :
					print "File Doesnot exist"
			elif cmd[0] == "get":
				filename=cmd[2]
				clientsocket.send(msg)
			elif cmd[0] == "bye":
				print
		else:
			print "Use the following:\n1)put address filename\n2)get put address filename\n3)bye b b-exit\n"	
	else:
		print "Use file"
	return filename
#--------------------------------------------------------------------------------

#TCP Bandwidth-------------------------------------------------------------------
def tcpbandwidth():
	host=sys.argv[1]
	port = 5003
	#Client socket
	tcpsendsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	tcpsendsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	#Creating a thread
	thread=tcpbw(tcpsendsock)
	#Starting a thread
	thread.start()	
#--------------------------------------------------------------------------------
#Voip request--------------------------------------------------------------------
def voiprequest(sock):
	thread=voiprecv(sock,5202)
	thread.start()
	thread1=voipstart(sock,5203)
	thread1.start()
def voipsrt(sock):
	thread1=voiprecv(sock,5203)
	thread1.start()
	thread=voipstart(sock,5202)
	thread.start()
#Menu---------------------------------------------------------------------------------
def menu():
	print "\nGive correct command words"
	print "                 1) Login - login"
	print "                 2) Logout - logout"
	print "                 3) List - list"
	print "                 4) Chat "
	print " 			a) Sending a message - send addr filename  "
	print "			b) Broadcast - broadcast message"
	print "                 5) File Transfer - file"
	print " 			a) Download file - get addr file"
	print " 			b) Upload file - put addr file"
	print "                 6) TCP Bandwidth - tcp"
	print "			7) Voip (all functions will be stopped) - voip addr"
	print "                 8) Exit -exit"	
def filemenu():
	print "Use the following:\n1)put address filename\n2)get put address filename\n3)bye b b-exit\n"
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if (len(sys.argv)<3):
		print "\nProvide hostname and port"
		sys.exit()
#global host 
host=sys.argv[1]
port = int(sys.argv[2])

#Client socket
clientsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

#Connecting to server
clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
	clientsocket.connect((host,port))
except:
	print "Unable to connect"
	sys.exit()
#Adding socket to the List
menu()
SOCKET_LIST=[sys.stdin,clientsocket]
while 1:
	#Monitoring the sockets
	ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST , [], [])
	for sock in ready_to_read:
		#Recieved a data from the server---------------------------------------------------------------------------------------------------------------------------------------------
		if sock == clientsocket:
			data = sock.recv(1024)
			r=data.split()
			req=r[0]
			if not data:
				print "\nLost from server"
				sys.exit()
			#put method
			elif req == "sendfile":
				#Transfer the file required
				filesendsock()
			elif req == "recievefile":
				#Recieve a File
				#print "Requisation"				
				filerecievesock()
			#Get method			
			elif req == "filerequest":
				filename = r[1]
				filesendsock()
			#TCP bandwidth
			elif req == "tcp":
				tcpbandwidth()
			#Voip connect
			elif req == "VOIP-request":
				print "Voip server"				
				voiprequest(sock)
			elif req == "startvoip":
				print "voip client"
				voipsrt(sock)
			else:
				#Response from the server
				os.system('clear')				
				print data 
				sys.stdout.flush()
				handle = open("recieveddata.txt",'wb')
				handle.write(data)
				menu()
		#Input from the user-----------------------------------------------------------------------------------------------------------------------------------------------------------
		else:
			msg = raw_input()
			msg1 =msg.lower()
			temp=msg1.split()
			msg1=temp[0]
			#print msg1
			#Login request from the user the decison helps the member to login back to the server
			if msg1 == "login":
				os.system('clear')
				clientsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
				clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				try:
					clientsocket.connect((host,port))
				except:
					print "\nUnable to connect"
					sys.exit()
				a=0
				menu()				
				SOCKET_LIST.append(clientsocket)
			#The decision helps to logout from the server
			elif msg1 == "logout":
				os.system('clear')
				menu()
				clientsocket.close()
				a=1
				SOCKET_LIST.remove(clientsocket)
			#Exit from the application
			elif msg1 == "exit":
				sys.exit()
			#Transferring file to a client
			elif msg1 == "file":
				os.system('clear')
				filemenu()
				filename=filehandler(msg,clientsocket)
			#Broadcasting a message
			elif msg1 == "broadcast":
				os.system("clear")				
				l=msg.split()
				x=len(l)
				if x==2:
					clientsocket.send(msg)
				else:
					print "\nUse broadcast message"
				menu()
			#Defining a list
			elif msg1 == "list":
				os.system('clear')
						
				l=msg.split()
				print l
				x=len(l)
				if x==1:
					clientsocket.send(msg)
				else:
					print "\nUse list"
				menu()			
				
			#Sendng a message to a client
			elif msg1 == "send":
				os.system('clear')
				l=msg.split()
				x=len(l)
					
				if x>=3:
					clientsocket.send(msg)
				else:
					print "\nUse send address message"
				menu()
			#TCP Bandwidth
			elif msg1 == "tcp":
				os.system('clear')
				clientsocket.send("tcp")
				#tcpbandwidth()
			#Improper commands
			elif msg1 == "voip":
				print "All function will be stopped"
				l=msg.split()
				x=len(l)
				if x == 2:
					voipip=l[1]
					clientsocket.send(msg)
				else :
					print "\n Use voip address"			
			else :
				menu()
