# -*- coding: utf-8 -*-

import sys,datetime,logging
import logging.handlers
import os.path

loggingLevelMapping = {
			'debug'    : logging.DEBUG,
			'info'     : logging.INFO,
			'error'    : logging.ERROR,
			'warn'     : logging.WARN,
			'warning'  : logging.WARNING,
			'critical' : logging.CRITICAL,
			'fatal'    : logging.FATAL,
		}

class CLog:

	def __init__(self):
		self.initialised = False
		
	def Init(self, logfile_name, level='info', stdout_log=True ):
		logfile_name = os.path.expandvars( logfile_name )
		filehandler = logging.handlers.RotatingFileHandler(logfile_name, maxBytes=1048576, backupCount=5) # 1MB files
		if stdout_log:
			streamhandler =  logging.StreamHandler(sys.stderr)
		else:
			streamhandler =  logging.handlers.NullHandler()
		formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
		streamhandler.setFormatter( formatter )
		filehandler.setFormatter( formatter )
		self.logger = logging.getLogger('main')
		self.logger.addHandler(streamhandler)
		self.logger.addHandler(filehandler)
		self.logger.setLevel( loggingLevelMapping[level] )
		
		self.initialised = True
		self.logger.info( 'session started' )

	def _prepare(self,msg,prefix=None):
		if prefix:
			msg = '[%s] %s'%(prefix,msg)
		if not self.initialised:
			sys.stderr.write( str(msg) + 'Logger not initialised\n' )
			return 'WARGH! logging is NOT initialised'
		return msg

	def Error(self, msg,prefix=None):
		self.logger.error( self._prepare( msg ) )

	def Info(self, msg,prefix=None):
		self.logger.info( self._prepare( msg ) )
		
	def Except(self,e):
		self.logger.exception( e )

Log = CLog()

def loaded(t, log=Log):
	log.Info( t, "LOADED" )

def reloaded(t, log=Log):
	log.Info( t, "RELOADED" )

def notice(t, log=Log):
	log.Info( t )

def error(t, log=Log):
	log.Error( t )

def good(t, log=Log):
	log.Info( t, "GOOD" )

def bad(t, log=Log):
	log.Error( t,"BAD" )
