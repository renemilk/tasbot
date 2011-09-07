from Main import MainApp as DefaultApp
import sys
version=(0,2,2)

#pretty sure there's buitins for this but I couldn't find them
def _greater(a,b):
	return cmp(a,b) > 0
def _less(a,b):
	return cmp(a,b) < 0
	
def _compare(vtuple,op):
	for i in range(len(vtuple)):
		if op(version[i], vtuple[i]):
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

