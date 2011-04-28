# -*- coding: utf-8 -*-
from customlog import Log
import sys
import traceback
import inspect
import ctypes
import plugins
def _async_raise(tid, exctype):
    '''Raises an exception in the threads with id tid'''
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        Log.Error("Cannot kill thread %i" % tid)
    if res != 1:
        # """if it returns a number greater than one, you're in trouble, 
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
        
class IPlugin(object):
	def __init__(self,name,tasclient):
		self.tasclient = tasclient
		self.name = name
		self.logger = Log.getPluginLogger( name )
	
class PluginHandler(object):
	def __init__(self,main):
		self.app = main
		self.plugins = dict()
		self.pluginthreads = dict()

	def addplugin(self,name,tasc):
		if name in self.plugins:
			Log.bad("Plugin %s is already loaded" % name)
			return
		try:
			code = __import__(name)
		except ImportError, imp:
			Log.Error("Cannot load plugin   "+name)
			Log.Except( imp )
			return
		try:
			self.plugins.update([(name,code.Main(name,tasc))])
		except TypeError, t:
			self.plugins.update([(name,code.Main())])
			Log.Error( 'loaded old-style plugin %s. Please derive from IPlugin'%name)
		self.pluginthreads.update([(name,[])])
		
		self.plugins[name].threads = self.pluginthreads[name]
		self.plugins[name].socket = tasc.socket
		#print "Pluging %s has %s functions" % (name,str(dir(self.plugins[name])))
		
		try:
			if "onload" in dir(self.plugins[name]):
				self.plugins[name].onload(tasc)
			if "onloggedin" in dir(self.plugins[name]) and self.app.connected:
				self.plugins[name].onloggedin(tasc.socket)
		except Exception, e:
			Log.Except( e )
			return
		Log.loaded("Plugin " + name)
	def unloadplugin(self,name):
		if not name in self.plugins:
			Log.Error("Plugin %s not loaded"%name)
			return
		try:
			if "ondestroy" in dir(self.plugins[name]):
				self.plugins[name].ondestroy()
			Log.notice("Killing any threads spawned by the plugin...")
			for tid in self.pluginthreads[name]:
				_async_raise(tid,SystemExit)
			self.pluginthreads.pop(name)
			self.plugins.pop(name)
			Log.notice("%s Unloaded" % name)
		except:
			Log.Error("Cannot unload plugin   "+name)
			Log.Error("Use forceunload to remove it anyway")
			Log.Error( traceback.print_exc() )
			
	def unloadAll(self):
		#make copy because unload changes the dict
		names = [ name for name in self.plugins ]
		for name in names:
			self.unloadplugin(name)

	def forceunloadplugin(self,name,tasc):
		if not name in self.plugins:
			Log.Error("Plugin %s not loaded"%name)
			return
		self.plugins.pop(name)
		Log.bad("%s UnLog.loaded(Forced)" % name)
	def reloadplugin(self,name):
		if not name in self.plugins:
			Log.Error("Plugin %s not loaded"%name)
			return
		try:
			if "ondestroy" in dir(self.plugins[name]):
				self.plugins[name].ondestroy()
			Log.notice("%s Unloaded" % name)
		except:
			Log.Error("Cannot unload plugin   "+name)
			Log.Error("Use forceunload to remove it anyway")
			Log.Error( traceback.print_exc() )
		try:
			code = reload(sys.modules[name])
		except:
			Log.Error("Cannot reload plugin %s!" % name)
			return
		Log.notice("Killing any threads spawned by the plugin...")
		for tid in self.pluginthreads[name]:
			_async_raise(tid,SystemExit)
		self.plugins.update([(name,code.Main())])
		self.pluginthreads.update([(name,[])])
		self.plugins[name].threads = self.pluginthreads[name]
		self.plugins[name].socket = self.app.tasclient.socket
		#print "Pluging %s has %s functions" % (name,str(dir(self.plugins[name])))
		
		try:
			if "onload" in dir(self.plugins[name]):
				self.plugins[name].onload(self.app.tasclient)
		except:
			Log.Error("Cannot load plugin   "+name)
			Log.Error( traceback.print_exc() )
			return
		Log.loaded("Plugin " + name)

	def forall(self,func_name,*args):
		Log.Info( 'forall %s'%func_name)
		for name,plugin in filter(lambda (name,plugin): func_name in dir(plugin), self.plugins.iteritems() ):
			try:
				func = getattr(plugin,func_name)
				func( *args )
			except SystemExit:
				raise SystemExit(0)
			except Exception,e :
				Log.Error("PLUGIN %s ERROR calling  %s"%(func_name,name))
				Log.Except( e )
				
	def onconnected(self):
		self.forall( "onconnected" )
			
	def ondisconnected(self):
		self.forall( "ondisconnected")
		
	def onmotd(self,content):
		self.forall( "onmotd", content)

	def onsaid(self,channel,user,message):
		self.forall( "onsaid",channel,user,message)

	def onsaidex(self,channel,user,message):
		self.forall( "onsaidex",channel,user,message)

	def onsaidprivate(self,user,message):
		args = message.split(" ")
		if args[0].lower() == "!reloadconfig" and user in self.app.admins:
			self.app.ReloadConfig()
		if args[0].lower() == "!unloadplugin" and user in self.app.admins and len(args) == 2:
			try:
				self.unloadplugin(args[1])
			except:
				Log.bad("Unloadplugin failed")
				Log.Error( traceback.print_exc() )

		if args[0].lower() == "!loadplugin" and user in self.app.admins and len(args) == 2:
			try:
				self.addplugin(args[1],self.app.tasclient)
			except:
				Log.bad("addplugin failed")
				Log.Error( traceback.print_exc() )

		if args[0].lower() == "!reloadplugin" and user in self.app.admins and len(args) == 2:
			try:
				self.reloadplugin(args[1])
			except:
				Log.bad("Unloadplugin failed")
				Log.Error( traceback.print_exc() )

		self.forall( "onsaidprivate",user,message)

	def onloggedin(self,socket):
		self.forall( "onloggedin",socket)

	def onpong(self):
		self.forall( "onpong" )
		
	def oncommandfromserver(self,command,args,socket):
		self.forall( "oncommandfromserver",command,args,socket)

	def onexit(self):
		self.forall( "onexit" )
		
	def ondisconnected(self):
		self.forall( "ondisconnected" )
