import warnings
import functools

from customlog import Log

def deprecated(alt='no alternative given'):
	"""This is a decorator which can be used to mark functions
	as deprecated. It will result in a warning being emitted
	when the function is used."""
	def depracted_decorator(func):
		func.decorated = True
		@functools.wraps(func)
		def new_func(*args, **kwargs):
			Log.debug( warnings.formatwarning("Call to deprecated function %(funcname)s.\nUse %(alt)s instead" % {
							'funcname': func.__name__,
							'alt':alt },
						DeprecationWarning,
						func.func_code.co_filename,
						func.func_code.co_firstlineno + 1, "" )
				)
			return func(*args, **kwargs)
		return new_func
	return depracted_decorator


def check_and_mark_decorated(func):
	"""Check if function was already decorated and mark decorated if it wasn't."""
	if 'decorated' in dir(func):
		return True
	func.decorated = True
	return False