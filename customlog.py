# -*- coding: utf-8 -*-

import sys,datetime

class CLog:

	def __init__(self):
		self.initialised = False
		
	def Init(self, logfile_name, error_log_name='log.err', errors_to_stderr=True, info_to_stdout=False ):
		self.errors_to_stderr = errors_to_stderr
		self.info_to_stdout = info_to_stdout
		self.logfile = open( logfile_name, 'a' )
		assert self.logfile, 'couldn\'t open logfile %s'%logfile_name
		if error_log_name != logfile_name:
			self.errfile = open( error_log_name, 'a' )
			assert self.errfile, 'couldn\'t open logfile %s'%error_log_name
		else:
			self.errfile = self.logfile
		self.initialised = True
		self.Info( 'session started' )
		if error_log_name != logfile_name:
			self.Error( 'session started' )


	def Error(self, msg,prefix=None):
		if prefix:
			msg = '[%s] %s'%(prefix,msg)
		if not self.initialised:
			sys.stderr.write( str(msg) + 'Logger not initialised\n' )
			return
		now = datetime.datetime.now()
		if isinstance( msg, list ):
			msg = '\n'.join( msg )
		msg = "%s:\t%s\n"%(now,msg)
		if self.errors_to_stderr:
			sys.stderr.write( msg )
		self.errfile.write( msg )
		self.errfile.flush()

	def Info(self, msg,prefix=None):
		if prefix:
			msg = '[%s] %s'%(prefix,msg)
		if not self.initialised:
			sys.stdout.write( str(msg) + 'Logger not initialised\n' )
			return
		now = datetime.datetime.now()
		if isinstance( msg, list ):
			msg = '\n'.join( msg )
		msg = "%s:\t%s\n"%(now,msg)
		if self.info_to_stdout:
			sys.stdout.write( msg )
		self.logfile.write( msg )
		self.logfile.flush()

Log = CLog()

def loaded(t, log=Log):
	log.Info( "[LOADED] "+t )

def reloaded(t, log=Log):
	log.Info( "[RELOADED] "+t )

def notice(t, log=Log):
	log.Info( "[NOTICE] "+t )

def error(t, log=Log):
	log.Error( "[ERROR ] "+t )

def good(t, log=Log):
	log.Info( "[ GOOD ] "+t )

def bad(t, log=Log):
	log.Error( "[ BAD  ] "+t )
