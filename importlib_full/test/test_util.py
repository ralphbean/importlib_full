from __future__ import with_statement
from importlib_full import util
from . import util as test_util
import imp
import sys
import types
import unittest


class ModuleForLoaderTests(unittest.TestCase):

    u"""Tests for importlib_full.util.module_for_loader."""

    def return_module(self, name):
        fxn = util.module_for_loader(lambda self, module: module)
        return fxn(self, name)

    def raise_exception(self, name):
        def to_wrap(self, module):
            raise ImportError
        fxn = util.module_for_loader(to_wrap)
        try:
            fxn(self, name)
        except ImportError:
            pass

    def test_new_module(self):
        # Test that when no module exists in sys.modules a new module is
        # created.
        module_name = u'a.b.c'
        with test_util.uncache(module_name):
            module = self.return_module(module_name)
            self.assertTrue(module_name in sys.modules)
        self.assertTrue(isinstance(module, types.ModuleType))
        self.assertEqual(module.__name__, module_name)

    def test_reload(self):
        # Test that a module is reused if already in sys.modules.
        name = u'a.b.c'
        module = imp.new_module(u'a.b.c')
        with test_util.uncache(name):
            sys.modules[name] = module
            returned_module = self.return_module(name)
            self.assertIs(returned_module, sys.modules[name])

    def test_new_module_failure(self):
        # Test that a module is removed from sys.modules if added but an
        # exception is raised.
        name = u'a.b.c'
        with test_util.uncache(name):
            self.raise_exception(name)
            self.assertTrue(name not in sys.modules)

    def test_reload_failure(self):
        # Test that a failure on reload leaves the module in-place.
        name = u'a.b.c'
        module = imp.new_module(name)
        with test_util.uncache(name):
            sys.modules[name] = module
            self.raise_exception(name)
            self.assertIs(module, sys.modules[name])


class SetPackageTests(unittest.TestCase):


    u"""Tests for importlib_full.util.set_package."""

    def verify(self, module, expect):
        u"""Verify the module has the expected value for __package__ after
        passing through set_package."""
        fxn = lambda: module
        wrapped = util.set_package(fxn)
        wrapped()
        self.assertTrue(hasattr(module, u'__package__'))
        self.assertEqual(expect, module.__package__)

    def test_top_level(self):
        # __package__ should be set to the empty string if a top-level module.
        # Implicitly tests when package is set to None.
        module = imp.new_module(u'module')
        module.__package__ = None
        self.verify(module, u'')

    def test_package(self):
        # Test setting __package__ for a package.
        module = imp.new_module(u'pkg')
        module.__path__ = [u'<path>']
        module.__package__ = None
        self.verify(module, u'pkg')

    def test_submodule(self):
        # Test __package__ for a module in a package.
        module = imp.new_module(u'pkg.mod')
        module.__package__ = None
        self.verify(module, u'pkg')

    def test_setting_if_missing(self):
        # __package__ should be set if it is missing.
        module = imp.new_module(u'mod')
        if hasattr(module, u'__package__'):
            delattr(module, u'__package__')
        self.verify(module, u'')

    def test_leaving_alone(self):
        # If __package__ is set and not None then leave it alone.
        for value in (True, False):
            module = imp.new_module(u'mod')
            module.__package__ = value
            self.verify(module, value)


def test_main():
    from test import test_support as support
    support.run_unittest(ModuleForLoaderTests, SetPackageTests)


if __name__ == u'__main__':
    test_main()
