# -*- coding: utf-8 -*-
import string, traceback, os
from customlog import *
import os.path

def readconfigfile(filename):
	try:
		with open(filename,"r") as f:
			entries = dict()
			s1 = f.read()
			s2 = ""
			for l in s1.replace("\r","").split("\n"):
				if not l.strip(" \t").startswith("---"):
					if l.count("---") == 0:
						s2 += l+ "\n"
					else:
						h = l.split("---")
						s2 += h[0]+ "\n"
			s = s2.strip(" \n\r\t;").replace("\r\n","")
			f.close()
			j = s.split(";")
			
			for entry in j:
				ed = entry.split("=")
				if len(ed) >= 2:
					entries.update([(ed[0].lower().strip(" \n\r\t;").replace("\r\n",""),"=".join(ed[1:]).strip(" \n\r\t;").replace("\r\n",""))])
				else:
					Log.Error("Invalid line on config file %s :\n\t%s" % ( filename , entry ) + normal)
			#Log.good("Loaded config file %s succesfully, %i entries" % (filename,len(entries)))
			return entries
	except:
		Log.Error("Error reading config file "+filename)
		return dict()

def writeconfigfile(filename,entries):
	with open(filename,"w") as f:
		for entry in entries:
			f.write("%s=%s;\n" % (entry.lower().strip(),entries[entry].strip()))

def parselist(string,sep):
	if string.count(sep) < 1:
		return [string]
	j = string.split(sep)
	l = []
	for i in j:
		l.append(os.path.expandvars(i.strip()))
	return l
			
class Config:
	def __init__( self, filename ):
		self.config = readconfigfile( filename )
		self.filename = filename

	def GetSingleOption( self, key, default ):
		if key in self.config:
			return os.path.expandvars(self.config[key])
		return default

	def GetOptionList( self, key, seperator=',',default=[] ):
		if key in self.config:
			return parselist( self.config[key], seperator )
		return default

	def __getitem__(self, key):
		val = self.GetSingleOption( key, ' ' )
		if not val:
			Log.Error( "key %s not found in %s"%(key,self.filename), 'Config' )
			raise Exception
		return val

	def write(self, filename):
		writeconfigfile( filename, self.config)