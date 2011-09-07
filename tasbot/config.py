# -*- coding: utf-8 -*-
import string
import traceback
import os
from ConfigParser import SafeConfigParser as ConfigParser
from ConfigParser import NoOptionError
import traceback

from customlog import Log


class Config:
	def __init__(self, filename):
		self._filename = filename
		self._config = ConfigParser()
		try:
			open(filename, 'r').close()
			self._config.read(filename)
		except Exception, e:
			try:
				Log.error("Configfile %s invalid" % self.filename)
				Log.exception(e)
			except AttributeError, e:
				print('Error reading configfile %s and Logging not initialized' %
						filename)
			raise SystemExit(1)

	def get(self, section, key, default=None):
		#find out reason why int keys fil to load
		key = str(key)
		#if isinstance(key,int):#uncomment this to locate int keys
			#Log.error('WUT')
			#traceback.print_stack()
			#raise SystemExit(1)
		try:
			return os.path.expandvars(self._config.get(section, key))
		except NoOptionError:
			if default == None:
				Log.error('no value or default found for config item %s -- %s' %
							(section, key))
		except Exception, e:
			Log.error('Error getting config item %s -- %s' %
							(section, key))
			Log.exception(e)
		return default

	GetSingleOption = get

	def set(self, section, key, value):
		self._config.set(section, key, value)

	def get_optionlist(self, section, key, seperator=',', default=[]):
		try:
			return self._parselist(self._config.get(section, key), seperator)
		except Exception, e:
			Log.error('Error getting value list for key %s in section %s' %
							(key, section))
			Log.exception(e)
		return default

	GetOptionList = get_optionlist

	def write(self, filename=self._filename):
		with open(filename, 'wb') as cfile:
			self._config.write(cfile)

	def _parselist(self, string, sep):
		if string.count(sep) < 1:
			return [string]
		return [os.path.expandvars(token.strip()) for token in string.split(sep)]
