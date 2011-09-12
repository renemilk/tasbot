# -*- coding: utf-8 -*-
import sys
import traceback
import inspect
import ctypes
import threading
import functools

from customlog import Log
import plugins


def _async_raise(tid, exctype):
	'''Raises an exception in the threads with id tid (never seen working)'''
	if not inspect.isclass(exctype):
		raise TypeError("Only types can be raised (not instances)")
	res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid,
				ctypes.py_object(exctype))
	if res == 0:
		Log.error("Cannot kill thread %i" % tid)
	if res != 1:
		#if it returns a number greater than one, you're in trouble,
		#and you should call it again with exc=NULL to revert the effect
		ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)


class PluginThread(threading.Thread):
	"""tiny wrapper to execute function with args in a thread"""
	def __init__(self, func, *args):
		super(PluginThread, self).__init__()
		self.func = func
		self.args = args

	def run(self):
		self.func(*self.args)


class Command(object):
	def __init__(self, trigger, min_no_args, access=(lambda args: True)):
		self.trigger = trigger
		self.min_no_args = min_no_args
		self.access = access


class ThreadContainer(object):
	def __init__(self):
		super(ThreadContainer, self).__init__()
		self.dying = False
		self.threads = []
		self.logger = Log

	def ondestroy(self):
		"""tell myself i'm dying and try to stop all my threads"""
		self.dying = True
		try:
			for thread in self.threads:
				try:
					thread.join(5)
				except AttributeError:
					#if its an old style id still try to terminate it (will prolly fail tho)
					_async_raise(thread, SystemExit)
		except Exception, e:
			self.logger.error("detroying %s plugin failed" % self.name)
			self.logger.exception(e)
		self.threads = filter(lambda thread: isinstance(thread,
				PluginThread) and thread.isAlive(), self.threads)
		if len(self.threads):
			self.logger.error("%d threads left alive after destroy was called" %
					len(self.threads))

	def start_thread(self, func, *args):
		"""run a given function with args in a
		new thread that is added to an internal list"""
		self.threads.append(PluginThread(func, *args))
		#app exits if only daemon threads are left alive
		self.threads[-1].daemon = True
		self.threads[-1].start()


class IPlugin(ThreadContainer):
	"""base class all plugins should derive from (and expose fitting ctor)"""
	def __init__(self, name, tasclient):
		super(IPlugin, self).__init__()
		self.tasclient = tasclient
		self.name = name
		self.logger = Log.getPluginLogger(name)
	
	@staticmethod
	def _admin_only(func):
		def decorated(self, args, socket):
			if self.tasclient.main.is_admin(args[1]):
				func(self, args, socket)
		return decorated

	@staticmethod
	def _not_self(func):
		"""This decorator will only call the decorated function if user is not myname"""
		def decorated(self, args, socket):
			if not self.tasclient.main.is_me(args[1]):
				return func(self, args, socket)
		return decorated


class PluginHandler(object):
	""" manage runtime loaded modules (plugins) """

	def __init__(self, main):
		super(PluginHandler, self).__init__()
		self.app = main
		self.plugins = dict()
		self.pluginthreads = dict()

	def addplugin(self, name, tasc):
		"""try to import module name and init it"""
		if name in self.plugins:
			Log.bad("Plugin %s is already loaded" % name)
			return
		try:
			code = __import__(name)
		except ImportError, imp:
			Log.error("Cannot load plugin %s" % name)
			Log.exception(imp)
			return
		try:
			self.plugins.update([(name, code.Main(name, tasc))])
		except TypeError, t:
			self.plugins.update([(name, code.Main())])
			Log.error('loaded old-style plugin %s. Please derive from IPlugin' % name)
		self.plugins[name].socket = tasc.socket

		try:
			if "onload" in dir(self.plugins[name]):
				self.plugins[name].onload(tasc)
			if "onloggedin" in dir(self.plugins[name]) and self.app.connected:
				self.plugins[name].onloggedin(tasc.socket)
		except Exception, e:
			Log.exception(e)
			return
		Log.loaded("Plugin " + name)

	def unloadplugin(self, name):
		""" unload plugin, stop all its threads
		via ondestroy and remove from interal list"""
		if not name in self.plugins:
			Log.error("Plugin %s not loaded" % name)
			return
		try:
			if "ondestroy" in dir(self.plugins[name]):
				self.plugins[name].ondestroy()
			self.plugins.pop(name)
			Log.notice("%s Unloaded" % name)
		except Exception, e:
			Log.error("Cannot unload plugin %s" % name)
			Log.error("Use forceunload to remove it anyway")
			Log.exception(e)

	def unloadAll(self):
		"""convenience function to unload all plugins at once"""
		#make copy because unload changes the dict
		names = [name for name in self.plugins]
		for name in names:
			self.unloadplugin(name)

	def forceunloadplugin(self, name, tasc):
		"""simply removes name from internal list, only call if unload else fails"""
		if not name in self.plugins:
			Log.error("Plugin %s not loaded" % name)
			return
		self.plugins.pop(name)
		Log.bad("%s UnLog.loaded(Forced)" % name)

	def reloadplugin(self, name):
		"""broken"""
		if not name in self.plugins:
			Log.error("Plugin %s not loaded" % name)
			return
		try:
			if "ondestroy" in dir(self.plugins[name]):
				self.plugins[name].ondestroy()
			Log.notice("%s Unloaded" % name)
		except Exception:
			Log.error("Cannot unload plugin %s" % name)
			Log.error("Use forceunload to remove it anyway")
			Log.error(traceback.print_exc())
		try:
			code = reload(sys.modules[name])
		except Exception:
			Log.error("Cannot reload plugin %s!" % name)
			return
		self.plugins.update([(name, code.Main())])
		self.plugins[name].socket = self.app.tasclient.socket
		try:
			if "onload" in dir(self.plugins[name]):
				self.plugins[name].onload(self.app.tasclient)
		except Exception:
			Log.error("Cannot load plugin   " + name)
			Log.error(traceback.print_exc())
			return
		Log.loaded("Plugin " + name)

	def forall(self, func_name, *args, **kwargs):
		""" execute a given function(name) on all plugins that expose it"""
		for name, plugin in filter(lambda (name, plugin):
				func_name in dir(plugin), self.plugins.iteritems()):
			try:
				func = getattr(plugin, func_name)
				func(*args, **kwargs)
			except SystemExit:
				raise SystemExit(0)
			except Exception, e:
				Log.error("PLUGIN %s ERROR calling  %s" %
					(func_name, name))
				Log.exception(e)

	def onconnected(self):
		self.forall("onconnected")

	def ondisconnected(self):
		self.forall("ondisconnected")

	def onmotd(self, content):
		self.forall("onmotd", content)

	def onsaid(self, channel, user, message):
		self.forall("onsaid", channel, user, message)

	def onsaidex(self, channel, user, message):
		self.forall("onsaidex", channel, user, message)

	def onsaidprivate(self, user, message):
		"""react on a few given keywords and also pass the call to all plugins"""
		args = message.split(" ")
		if args[0].lower() == "!reloadconfig" and user in self.app.admins:
			self.app.ReloadConfig()
		if (args[0].lower() == "!unloadplugin" and
				user in self.app.admins and len(args) == 2):
			try:
				self.unloadplugin(args[1])
			except Exception:
				Log.bad("Unloadplugin failed")
				Log.error(traceback.print_exc())

		if (args[0].lower() == "!loadplugin" and
				user in self.app.admins and len(args) == 2):
			try:
				self.addplugin(args[1], self.app.tasclient)
			except Exception:
				Log.bad("addplugin failed")
				Log.error(traceback.print_exc())

		if (args[0].lower() == "!reloadplugin" and
				user in self.app.admins and len(args) == 2):
			try:
				self.reloadplugin(args[1])
			except Exception:
				Log.bad("Unloadplugin failed")
				Log.error(traceback.print_exc())

		self.forall("onsaidprivate", user, message)

	def onloggedin(self, socket):
		self.forall("onloggedin", socket)

	def onpong(self):
		self.forall("onpong")

	def oncommandfromserver(self, command, args, socket):
		self.forall("oncommandfromserver", command, args, socket)

	def onexit(self):
		self.forall("onexit")

	def ondisconnected(self):
		self.forall("ondisconnected")
