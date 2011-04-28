# -*- coding: utf-8 -*-
from customlog import Log
import sys
import traceback
import inspect
import ctypes
import plugins
import threading

def _async_raise(tid, exctype):
    '''Raises an exception in the threads with id tid (never seen working)'''
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        Log.Error("Cannot kill thread %i" % tid)
    if res != 1:
        # """if it returns a number greater than one, you're in trouble, 
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
    
class PluginThread(threading.Thread):
	"""tiny wrapper to execute function with args in a thread"""
	def __init__(self, func, *args ):
		self.func = func
		self.args = args
		threading.Thread.__init__(self)
		
	def run(self):
		self.func( *self.args )
		
class IPlugin(object):
	"""base class all plugins should derive from (and expose fitting ctor)"""
	def __init__(self,name,tasclient):
		self.tasclient = tasclient
		self.name = name
		self.logger = Log.getPluginLogger( name )
		self.dying = False
		self.threads = []
		
	def ondestroy(self):
		"""tell myself i'm dying and try to stop all my threads"""
		self.dying = True
		
		try:
			for thread in self.threads:
				try:
					thread.join(5)
				except AttributeError:
					#if its an old style id still try to terminate it (will prolly fail tho)
					_async_raise( thread, SystemExit )
		except Exception, e:
			self.logger.Critical( "detroying %s plugin failed"%self.name)
			self.logger.Except( e )
		self.threads = filter( lambda thread: isinstance(thread, PluginThread) and thread.isAlive(), self.threads )
		if len(self.threads):
			self.logger.Error( "%d threads left alive after destroy was called" )
			
	def startThread(self,func,*args):
		"""run a given function with args in a new thread that is added to an internal list"""
		self.threads.append( PluginThread(func, *args) )
		#app exists if only daemon threads are left alive
		self.threads[-1].daemon = True
		self.threads[-1].start()
		
	
class PluginHandler(object):
	""" manage runtime loaded modules (plugins) """
	
	def __init__(self,main):
		self.app = main
		self.plugins = dict()
		self.pluginthreads = dict()

	def addplugin(self,name,tasc):
		"""try to import module name and init it"""
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
		self.plugins[name].socket = tasc.socket
		
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
		""" unload plugin, stop all its threads via ondestroy and remove from interal list"""
		if not name in self.plugins:
			Log.Error("Plugin %s not loaded"%name)
			return
		try:
			if "ondestroy" in dir(self.plugins[name]):
				self.plugins[name].ondestroy()
			self.plugins.pop(name)
			Log.notice("%s Unloaded" % name)
		except Exception, e:
			Log.Error("Cannot unload plugin   "+name)
			Log.Error("Use forceunload to remove it anyway")
			Log.Except( e )
			
	def unloadAll(self):
		"""convenience function to unload all plugins at once"""
		#make copy because unload changes the dict
		names = [ name for name in self.plugins ]
		for name in names:
			self.unloadplugin(name)

	def forceunloadplugin(self,name,tasc):
		"""simply removes name from internal list, only call if unload else fails"""
		if not name in self.plugins:
			Log.Error("Plugin %s not loaded"%name)
			return
		self.plugins.pop(name)
		Log.bad("%s UnLog.loaded(Forced)" % name)
		
	def reloadplugin(self,name):
		"""broken"""
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
		self.plugins.update([(name,code.Main())])
		self.plugins[name].socket = self.app.tasclient.socket
		
		try:
			if "onload" in dir(self.plugins[name]):
				self.plugins[name].onload(self.app.tasclient)
		except:
			Log.Error("Cannot load plugin   "+name)
			Log.Error( traceback.print_exc() )
			return
		Log.loaded("Plugin " + name)

	def forall(self,func_name,*args):
		""" execute a given function(name) on all plugins that expose it"""
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
		"""react on a few given keywords and also pass the call to all plugins"""
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
