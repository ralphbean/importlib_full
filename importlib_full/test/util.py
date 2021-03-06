from contextlib import contextmanager
import imp
import os.path
from test import test_support as support
import unittest
import sys


CASE_INSENSITIVE_FS = True
# Windows is the only OS that is *always* case-insensitive
# (OS X *can* be case-sensitive).
if sys.platform not in (u'win32', u'cygwin'):
    changed_name = __file__.upper()
    if changed_name == __file__:
        changed_name = __file__.lower()
    if not os.path.exists(changed_name):
        CASE_INSENSITIVE_FS = False


def case_insensitive_tests(test):
    u"""Class decorator that nullifies tests requiring a case-insensitive
    file system."""
    return unittest.skipIf(not CASE_INSENSITIVE_FS,
                            u"requires a case-insensitive filesystem")(test)


@contextmanager
def uncache(*names):
    u"""Uncache a module from sys.modules.

    A basic sanity check is performed to prevent uncaching modules that either
    cannot/shouldn't be uncached.

    """
    for name in names:
        if name in (u'sys', u'marshal', u'imp'):
            raise ValueError(
                u"cannot uncache {0} as it will break _importlib_full".format(name))
        try:
            del sys.modules[name]
        except KeyError:
            pass
    try:
        yield
    finally:
        for name in names:
            try:
                del sys.modules[name]
            except KeyError:
                pass

@contextmanager
def import_state(**kwargs):
    u"""Context manager to manage the various importers and stored state in the
    sys module.

    The 'modules' attribute is not supported as the interpreter state stores a
    pointer to the dict that the interpreter uses internally;
    reassigning to sys.modules does not have the desired effect.

    """
    originals = {}
    try:
        for attr, default in ((u'meta_path', []), (u'path', []),
                              (u'path_hooks', []),
                              (u'path_importer_cache', {})):
            originals[attr] = getattr(sys, attr)
            if attr in kwargs:
                new_value = kwargs[attr]
                del kwargs[attr]
            else:
                new_value = default
            setattr(sys, attr, new_value)
        if len(kwargs):
            raise ValueError(
                    u'unrecognized arguments: {0}'.format(kwargs.keys()))
        yield
    finally:
        for attr, value in originals.items():
            setattr(sys, attr, value)


class mock_modules(object):

    u"""A mock importer/loader."""

    def __init__(self, *names):
        self.modules = {}
        for name in names:
            if not name.endswith(u'.__init__'):
                import_name = name
            else:
                import_name = name[:-len(u'.__init__')]
            if u'.' not in name:
                package = None
            elif import_name == name:
                package = name.rsplit(u'.', 1)[0]
            else:
                package = import_name
            module = imp.new_module(import_name)
            module.__loader__ = self
            module.__file__ = u'<mock __file__>'
            module.__package__ = package
            module.attr = name
            if import_name != name:
                module.__path__ = [u'<mock __path__>']
            self.modules[import_name] = module

    def __getitem__(self, name):
        return self.modules[name]

    def find_module(self, fullname, path=None):
        if fullname not in self.modules:
            return None
        else:
            return self

    def load_module(self, fullname):
        if fullname not in self.modules:
            raise ImportError
        else:
            sys.modules[fullname] = self.modules[fullname]
            return self.modules[fullname]

    def __enter__(self):
        self._uncache = uncache(*self.modules.keys())
        self._uncache.__enter__()
        return self

    def __exit__(self, *exc_info):
        self._uncache.__exit__(None, None, None)
