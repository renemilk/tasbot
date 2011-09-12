import warnings
import functools

from customlog import Log

def deprecated(alt='no alternative given'):
	"""This is a decorator which can be used to mark functions
	as deprecated. It will result in a warning being emitted
	when the function is used."""
	def depracted_decorator(func):
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


def not_self(myname):
	"""This decorator will only call the decorated function if user is not myname"""
	def not_self_decorator(func):
		def new_func(*args, **kwargs):
			if args[1] != myname:
				return func(*args, **kwargs)
		return new_func
	return not_self_decorator
