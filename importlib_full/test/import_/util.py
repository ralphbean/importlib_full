import functools
import importlib_full
import importlib_full._bootstrap
import unittest


using___import__ = False


def import_(*args, **kwargs):
    u"""Delegate to allow for injecting different implementations of import."""
    if using___import__:
        return __import__(*args, **kwargs)
    else:
        return importlib_full.__import__(*args, **kwargs)


def importlib_full_only(fxn):
    u"""Decorator to skip a test if using __builtins__.__import__."""
    return unittest.skipIf(using___import__, u"importlib_full-specific test")(fxn)


def mock_path_hook(*entries, **_3to2kwargs):
    importer = _3to2kwargs['importer']; del _3to2kwargs['importer']
    u"""A mock sys.path_hooks entry."""
    def hook(entry):
        if entry not in entries:
            raise ImportError
        return importer
    return hook
