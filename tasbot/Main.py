#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, string, base64, hashlib, time, ParseConfig, thread, Plugin, traceback, Client, binascii
from customlog import *
from daemon import Daemon

class MainApp(Daemon):
	"""main application object that has creates tasclient, pluginhandler and PingLoop instances"""
	def PingLoop(self):
		"""sned a PING to the server every 10 seconds until either force_quit is true or i got into an error state"""
		while not self.force_quit and self.er == 0:
			self.tasclient.ping()
			time.sleep(10)
		raise SystemExit(0)
	
	def onlogin(self,socket):
		"""start PingLoop and client mainloop, connect event handlers"""
		if self.firstconnect == 1:
			thread.start_new_thread(self.tasclient.mainloop,())
			thread.start_new_thread(self.PingLoop,())
			self.firstconnect = 0

		#self.tasclient.events.ondisconnected = self.ph.ondisconnected

		self.tasclient.events.onmotd = self.ph.onmotd
		self.tasclient.events.onsaid = self.ph.onsaid
		self.tasclient.events.onsaidex = self.ph.onsaidex
		self.tasclient.events.onsaidprivate = self.ph.onsaidprivate
		self.tasclient.events.onpong = self.ph.onpong
		self.tasclient.events.oncommandfromserver = self.ph.oncommandfromserver
		self.tasclient.events.ondisconnected = self.ph.ondisconnected

		self.ph.onloggedin(socket)
		self.ph.oncommandfromserver("ACCEPTED",[],self.tasclient.socket)
		self.connected = True
		Log.good("Logged in")

	def SaveConfig(self):
		"""commit current config dictionary to file"""
		ParseConfig.writeconfigfile(self.configfile,self.config)

	def isAdmin(self,username):
		"""return true if either username or the asscoiated id is in self.admins"""
		if username in self.admins:
				return True
		elif username in self.tasclient.users:
				if "#"+str(self.tasclient.users[username].id) in self.admins:
						return True
				else:
						return False
		else:
				return False

	def Dologin(self):
		"""handle tasserver login"""
		if self.tasclient.flags.register:
			Log.notice("Not logging in because a registration is in progress")
			return
		if self.verbose:
			Log.notice("Logging in...")
		m = hashlib.md5()
		m.update(self.config["password"])
		phash = base64.b64encode(binascii.a2b_hex(m.hexdigest()))
		self.tasclient.login(self.config["nick"],phash,"Newbot",2400,self.config["lanip"] if "lanip" in self.config else "*")

	def Register(self,username,password):
		"""register new account on tasserver"""
		m = hashlib.md5()
		m.update(self.config["password"])
		self.tasclient.register(self.config["nick"],base64.b64encode(binascii.a2b_hex(m.hexdigest())))

	def destroy(self):
		"""deprecated"""
		self.tasclient.error = 1
		self.er = 1
		raise SystemExit(0)

	def ReloadConfig(self):
		"""reload config and admins from file"""
		self.config = ParseConfig.readconfigfile(self.configfile)
		self.admins = ParseConfig.parselist(self.config["admins"],",")

	def __init__(self,configfile,pidfile,register,verbose):
		"""default init and plugin loading"""
		super(MainApp, self).__init__(pidfile)
		self.firstconnect = 1
		self.er = 0
		self.connected = False
		self.cwd = os.getcwd()
		self.ph = Plugin.PluginHandler(self)
		self.configfile = configfile
		self.config = ParseConfig.readconfigfile(configfile)
		self.admins = ParseConfig.parselist(self.config["admins"],",")
		self.verbose = verbose
		self.reg = register
		self.tasclient = Client.Tasclient(self)

		for p in ParseConfig.parselist(self.config["plugins"],","):
			self.ph.addplugin(p,self.tasclient)

		self.tasclient.events.onconnectedplugin = self.ph.onconnected
		self.tasclient.events.onconnected = self.Dologin
		self.tasclient.events.onloggedin = self.onlogin
		self.force_quit = False
		

	def run(self):
		"""the main loop for MainApp, once this exists MainApp will be in unsable state"""
		while not self.force_quit:
			try:
				Log.notice("Connecting to %s:%i" % (self.config["serveraddr"],int(self.config["serverport"])))
				self.tasclient.connect(self.config["serveraddr"],int(self.config["serverport"]))
				while not self.force_quit:
					time.sleep(10)
			except SystemExit:
				break
			except KeyboardInterrupt:
				Log.Error("SIGINT, Exiting")
				self.ph.onexit()
				break
			except Exception, e:
				Log.Error("parsing command line")
				Log.Except( e )
			time.sleep(10)
		self.ph.onexit()
		self.ph.unloadAll()
		self.tasclient.disconnect()
		self.tasclient = None
