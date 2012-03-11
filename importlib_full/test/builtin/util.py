import sys

assert u'errno' in sys.builtin_module_names
NAME = u'errno'

assert u'importlib_full' not in sys.builtin_module_names
BAD_NAME = u'importlib_full'
