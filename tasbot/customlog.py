# -*- coding: utf-8 -*-

import sys,datetime,logging
import logging.handlers
import os.path
from color_formatter import *

loggingLevelMapping = {
			'debug'    : logging.DEBUG,
			'info'     : logging.INFO,
			'error'    : logging.ERROR,
			'warn'     : logging.WARN,
			'warning'  : logging.WARNING,
			'critical' : logging.CRITICAL,
			'fatal'    : logging.FATAL,
		}

class ILogger(object):
	def __init__(self,prefix=None):
		self.default_prefix = prefix
		
	def _prepare(self,msg,prefix):
		if prefix:
			msg = '[%s] %s'%(prefix,msg)
		if self.default_prefix:
			msg = '<%s> %s'%(self.default_prefix, msg)
		if not self.initialised:
			sys.stderr.write( str(msg) + 'Logger not initialised\n' )
			return 'WARGH! logging is NOT initialised'
		return msg

	def Error(self, msg,prefix=None):
		self.logger.error( self._prepare( msg,prefix ) )

	def Debug(self, msg,prefix=None):
		self.logger.debug( self._prepare( msg,prefix ) )
	def Info(self, msg,prefix=None):
		self.logger.info( self._prepare( msg,prefix ) )
		
	def Except(self,e):
		#TODO needs prefix handling
		self.logger.exception( e )
	
	def loaded(self,t):
		self.Info( t, "LOADED" )

	def reloaded(self,t):
		self.Info( t, "RELOADED" )

	def notice(self,t):
		self.Info( t )

	def good(self,t):
		self.Info( t, "GOOD" )

	def bad(self,t):
		self.Error( t,"BAD" )

class CLog(ILogger):

	def __init__(self):
		ILogger.__init__(self,None)
		self.initialised = False
		self.FORMAT = '$BOLD%(levelname)s$RESET - %(asctime)s - %(message)s'
		
	def Init(self, logfile_name, level='info', stdout_log=True ):
		logfile_name = os.path.expandvars( logfile_name )
		self.filehandler = logging.handlers.RotatingFileHandler(logfile_name, maxBytes=1048576, backupCount=5) # 1MB files
		if stdout_log:
			self.streamhandler =  logging.StreamHandler(sys.stderr)
		else:
			self.streamhandler =  logging.handlers.NullHandler()
		self.streamformatter = ColoredFormatter(formatter_message(self.FORMAT, True))
		self.fileformatter = ColoredFormatter(formatter_message(self.FORMAT, False))
		self.streamhandler.setFormatter( self.streamformatter )
		self.filehandler.setFormatter( self.fileformatter )
		self.logger = logging.getLogger('main')
		self.logger.addHandler(self.streamhandler)
		self.logger.addHandler(self.filehandler)
		self.logger.setLevel( loggingLevelMapping[level] )
		
		self.initialised = True
		self.logger.info( 'session started' )
	
	def getPluginLogger(self, name):
		return PrefixedLogger( self, name )

class PrefixedLogger(ILogger):
	def __init__(self, clog,name):
		ILogger.__init__(self, 'PL %s'%name)
		self.logger = clog.logger
		self.initialised = True

Log = CLog()

