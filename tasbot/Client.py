# -*- coding: utf-8 -*-
from socket import *
import string, re, time, utilities, sys, traceback
from utilities import *
from customlog import *

class User:
	def __init__(self,username,id,country,cpu):
			self.username = username
			self.id = id
			self.country = country
			self.cpu = cpu
			self.afk = False
			self.ingame = False
			self.mod = False
			self.rank = 0
			self.bot = False
			self.battleid = -1
	def clientstatus(self,status):
			self.afk = bool(getaway(int(status)))
			self.ingame = bool(getingame(int(status)))
			self.mod = bool(getmod(int(status)))
			self.bot = bool(getbot(int(status)))
			self.rank = getrank(status)-1

def parsecommand(cl,c,args,events,sock):
	if c.strip() != "":
		events.oncommandfromserver(c,args,sock)
		if c == "JOIN" and len(args) >= 1:
			if not args[0] in cl.channels:
				cl.channels.append(args[0])
				Log.good("Joined #"+args[0])
		if c == "FORCELEAVECHANNEL" and len(args) >= 2:
			if args[0] in cl.channels:
				cl.channels.remove(args[0])
				Log.bad("I've been kicked from #%s by <%s>" % (args[0],args[1]))
			else:
				Log.Error("I've been kicked from a channel that i haven't joined")
		if c == "TASSERVER":
			Log.good("Connected to server")

			if cl.fl.register:
				cl.register(cl.uname,cl.password)
				receive(cl,sock,events)
			else:
				events.onconnected()
		if c == "AGREEMENTEND":
			Log.notice("accepting agreement")
			sock.send("CONFIRMAGREEMENT\n")
			cl.login(cl.uname,cl.password,"BOT",2000)
			events.onloggedin(sock)
		if c == "MOTD":
			events.onmotd(" ".join(args))
		if c == "ACCEPTED":
			events.onloggedin(sock)
		if c == "DENIED" and ' '.join(args).lower().count("already") == 0:
			Log.Error("Login failed ( %s ), trying to register..." % ' '.join(args))
			Log.notice("Closing Connection")
			sock.close()
			cl.fl.register = True
			cl.connect(cl.lastserver,cl.lastport)

		if c == "REGISTRATIONACCEPTED":
			Log.good("Registered")
			Log.notice("Closing Connection")
			sock.close()
			cl.fl.register = False
			cl.connect(cl.lastserver,cl.lastport)
		if c == "PONG":
			cl.lpo = time.time()
			events.onpong()
		if c == "JOINEDBATTLE" and len(args) >= 2:
			try:
				cl.users[args[1]].battleid = int(args[0])
			except:
				Log.Error("Invalid JOINEDBATTLE Command from server: %s %s"%(c,str(args)))
				Log.Error( traceback.format_exc() )
		if c == "BATTLEOPENED" and len(args) >= 4:
			try:
				cl.users[args[3]].battleid = int(args[0])
			except:
				Log.Error("Invalid BATTLEOPENED Command from server: %s %s"%(c,str(args)))
				Log.Error( traceback.format_exc() )
		if c == "LEFTBATTLE" and len(args) >= 2:
			try:
				cl.users[args[1]].battleid = -1
			except:
				Log.Error("Invalid LEFTBATTLE Command from server: %s %s"%(c,str(args)))
				Log.Error( traceback.format_exc() )
		if c == "SAIDPRIVATE" and len(args) >= 2:
			events.onsaidprivate(args[0],' '.join(args[1:]))
		if c == "ADDUSER":
			try:
				if len(args) == 4:#Account id
					cl.users[args[0]] = User(args[0],int(args[3]),args[1],int(args[2]))
					#Log.notice(args[0]+":"+args[3])
				elif len(args) == 3:
					cl.users[args[0]] = User(args[0],int(-1),args[1],int(args[2]))
					#Log.notice(args[0]+":"+"-1")
				else:
					Log.Error("Invalid ADDUSER Command from server: %s %s"%(c,str(args)))
				Log.Debug('ADDUSER %d args: '%len(cl.users) + ' '.join( args ) )
			except:
				Log.Error("Invalid ADDUSER Command from server: %s %s"%(c,str(args)))
				Log.Error( traceback.format_exc() )
		if c == "REMOVEUSER":
			if len(args) == 1:
				if args[0] in cl.users:
					del cl.users[args[0]]
				else:
					Log.Error("Invalid REMOVEUSER Command: no such user"+args[0])
			else:
					Log.Error("Invalid REMOVEUSER Command: not enough arguments")
		if c == "CLIENTSTATUS":
			if len(args) == 2:
				if args[0] in cl.users:
					try:
						cl.users[args[0]].clientstatus(int(args[1]))
					except:
						Log.Error("Malformed CLIENTSTATUS")
						Log.Error( traceback.format_exc() )
				else:
					Log.Error("Invalid CLIENTSTATUS: No such user <%s>" % args[0])

def receive(cl,socket,events): #return commandname & args
	buf = ""
	try:
		while not buf.strip("\r ").endswith("\n"):
			#print "Receiving incomplete command..."
			nbuf =  socket.recv(512)
			if len(nbuf) == 0:
				return 1
			buf += nbuf
			if len(buf) > 1024*200:
			  Log.Error("Buffer size exceeded!!!")
			  return 1
	except:
		Log.Error("Connection Broken")
		return 1 # Connection broken
	commands = buf.strip("\r ").split("\n")
	for cmd in commands:
		c = cmd.split(" ")[0].upper()
		args = cmd.split(" ")[1:]
		parsecommand(cl,c,args,events,socket)
	return 0
class ServerEvents:
	def onconnected(self):
		Log.good("Connected to TASServer")
	def onconnectedplugin(self):
		Log.good("Connected to TASServer")
	def ondisconnected(self):
		Log.bad("Disconnected")
	def onmotd(self,content):
		Log.Info( "[MOTD] "+content )
	def onsaid(self,channel,user,message):
		Log.Info( "[CHANNEL] %s: <%s> %s"%(channel,user,message) )
	def onsaidex(self,channel,user,message):
		Log.Info( "[CHANNELEX] %s: <%s> %s"%(channel,user,message) )
	def onsaidprivate(self,user,message):
		Log.Info( "[PRIVATE] <%s> %s"%(user,message) )
	def onloggedin(self,socket):
		Log.Info( "[LOGIN] successful")
	def onpong(self):
		#print blue+"PONG"+normal
		pass
	def oncommandfromserver(self,command,args,socket):
		#print yellow+"From Server: "+str(command)+" Args: "+str(args)+normal
		pass
	def onexit(self):
	  pass
class Flags:
	norecwait = False
	register = False


class Tasclient:
	sock = 0
	flags = Flags()
	error = 0
	lp = 0.0
	lpo = 0.0
	users = dict()
	def mainloop(self):
		while 1:
			if self.er == 1:
				raise SystemExit(0)
			try:

				#print "Waiting data from socket"
				result = receive(self,self.sock,self.events)
				#print "Received data"
				if result == 1:
					self.events.ondisconnected()
					self.users = dict()
					Log.Error("SERVER: Timed out, reconnecting in 40 secs")
					self.main.connected = False
					if not self.flags.norecwait:
						time.sleep(40.0)
						self.flags.norecwait = False
					try:
						self.sock.close()
					except:
						pass
					self.sock = socket(AF_INET,SOCK_STREAM)
					self.sock.settimeout(40)
					self.sock.connect((self.lastserver,int(self.lastport)))
					receive(self,self.sock,self.events)
					self.main.connected = True
					self.events.onconnectedplugin()
			except SystemExit:
				raise SystemExit(0)
			except:
				Log.Error("Command Error")
				Log.Error( traceback.print_exc(file=sys.stdout) )
	def __init__(self,app):
		self.events = ServerEvents()
		self.main = app
		self.channels = []
	def connect(self,server,port):
		self.lastserver = server
		self.lastport = port

		while 1:
			try:
				self.sock = socket(AF_INET,SOCK_STREAM)
				self.sock.settimeout(40)
				self.sock.connect((server,int(port)))
				self.events.onconnectedplugin()
				if self.main.reg:
					Log.notice("Registering nick")
					self.main.Register(self.main.config["nick"],self.main.config["password"])
				res = receive(self,self.sock,self.events)
				if not res == 1:
					return
			except SystemExit:
				raise SystemExit(0)
			except:
				self.main.connected = False
				Log.Error("Cannot connect, retrying in 40 secs...")
				Log.Error( traceback.print_exc(file=sys.stdout) )
				if self.er == 1:
					raise SystemExit(0)
				time.sleep(40.0)

	def disconnect(self,hard=False):
		try:
			self.sock.send("EXIT\n")
		except:
			pass
		self.sock.close()
		self.sock = 0
	def login(self,username,password,client,cpu,lanip="*"):
		Log.notice("Trying to login with username %s " % (username))
		lanip = self.sock.getsockname()[0]
		#print "LOGIN %s %s %i * %s\n" % (username,password,cpu,client)
		try:
			self.sock.send("LOGIN %s %s %i %s %s\t0\t%s\n" % (username,password,cpu,lanip,client,"a sp"))
		except:
			Log.Error("Cannot send login command")
		self.uname = username
		self.password = password
		self.channels = []
		receive(self,self.sock,self.events)
	def register(self,username,password):
		try:
			Log.notice("Trying to register account")
			self.sock.send("REGISTER %s %s\n" % (username,password))
		except:
			Log.Error("Cannot send register command")
	def leave(self,channel): #Leaves a channel
		if channel in self.channels:
			try:
				self.sock.send("LEAVE %s\n" % channel)
				self.channels.remove(channel)
			except:
				Log.bad("Failed to send LEAVE command")
		else:
			Log.bad("leave(%s) : Not in channel" % channel)

	def join(self,channel):
		if not channel in self.channels:
			self.sock.send("JOIN %s\n" % channel)

	def say(self,channel,phrase):
		self.join(channel)
		self.sock.send("SAY %s %s\n" % (channel,phrase) )


	def ping(self):
		if self.er == 1:
			return
		try:
			self.sock.send("PING\n")
			self.lp = time.time()
		except:
			Log.Error("Cannot send ping command")
