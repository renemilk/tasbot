"""tasbot module docstring"""

__version__=(1,0,0)

from main import MainApp as DefaultApp
import sys

#pretty sure there's buitins for this but I couldn't find them
def _greater(a,b):
	return cmp(a,b) > 0
def _less(a,b):
	return cmp(a,b) < 0
	
def _compare(vtuple,op):
	for i in range(len(vtuple)):
		if op(__version__[i], vtuple[i]):
			return False
	return True
	
def check_min_version(vtuple):
	if not _compare(vtuple,_less):
		print('tasbot version %s does not match minimum requirement %s'%(str(version),str(vtuple)))
		sys.exit(1)
	
def check_max_version(vtuple):
	if not _compare(vtuple,_greater):
		print('tasbot version %s exceeds maximum requirement %s'%(str(version),str(vtuple)))
		sys.exit(1)

