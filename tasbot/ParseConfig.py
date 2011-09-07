# -*- coding: utf-8 -*-
import string, traceback, os
from customlog import *
import os.path
from ConfigParser import SafeConfigParser as ConfigParser
from ConfigParser import NoOptionError
import traceback
			
class Config:
	def __init__( self, filename ):
		self._filename = filename
		self._config = ConfigParser()
		try:
			open(filename,'r').close()
			self._config.read( filename )
		except Exception,e:
			try:
				Log.Error( "Configfile %s invalid"%self.filename)
				Log.Except( e )
			except AttributeError,e:
				print('Error reading configfile %s and Logging not initialized'%filename)
			raise SystemExit(1)

	def GetSingleOption( self, section, key, default=None ):
		#find out reason why int keys fil to load
		key=str(key)
		#if isinstance(key,int):#uncomment this to locate int keys
			#Log.Error('WUT')
			#traceback.print_stack()
			#raise SystemExit(1)
		try:
			#return self._config.get(section,key)
			return os.path.expandvars(self._config.get(section,key))
		except NoOptionError:
			if default==None:
				Log.Error( 'no value or default found for config item %s -- %s'%(section,key) )
		except Exception,e:
			Log.Error( 'Error getting config item %s -- %s'%(section,key) )
			Log.Except(e)
		return default
	get=GetSingleOption
		
	def set(self,section,key,value):
		self._config.set(section, key,value)
		

	def GetOptionList( self, section, key, seperator=',',default=[] ):
		try:
			return self._parselist( self._config.get(section,key), seperator )
		except Exception,e:
			Log.Error('Error getting value list for key %s in section %s'%(key,section) )
			Log.Except(e)
		return default

	def write(self, filename):
		with open(filename,'wb') as cfile:
			self._config.write(cfile)

	def _parselist(self,string,sep):
		if string.count(sep) < 1:
			return [string]
		return [os.path.expandvars(token.strip()) for token in string.split(sep)]