from __future__ import with_statement
from . import util
import imp
import importlib_full
import sys
import unittest


class ImportModuleTests(unittest.TestCase):

    u"""Test importlib_full.import_module."""

    def test_module_import(self):
        # Test importing a top-level module.
        with util.mock_modules(u'top_level') as mock:
            with util.import_state(meta_path=[mock]):
                module = importlib_full.import_module(u'top_level')
                self.assertEqual(module.__name__, u'top_level')

    def test_absolute_package_import(self):
        # Test importing a module from a package with an absolute name.
        pkg_name = u'pkg'
        pkg_long_name = u'{0}.__init__'.format(pkg_name)
        name = u'{0}.mod'.format(pkg_name)
        with util.mock_modules(pkg_long_name, name) as mock:
            with util.import_state(meta_path=[mock]):
                module = importlib_full.import_module(name)
                self.assertEqual(module.__name__, name)

    def test_shallow_relative_package_import(self):
        # Test importing a module from a package through a relative import.
        pkg_name = u'pkg'
        pkg_long_name = u'{0}.__init__'.format(pkg_name)
        module_name = u'mod'
        absolute_name = u'{0}.{1}'.format(pkg_name, module_name)
        relative_name = u'.{0}'.format(module_name)
        with util.mock_modules(pkg_long_name, absolute_name) as mock:
            with util.import_state(meta_path=[mock]):
                importlib_full.import_module(pkg_name)
                module = importlib_full.import_module(relative_name, pkg_name)
                self.assertEqual(module.__name__, absolute_name)

    def test_deep_relative_package_import(self):
        modules = [u'a.__init__', u'a.b.__init__', u'a.c']
        with util.mock_modules(*modules) as mock:
            with util.import_state(meta_path=[mock]):
                importlib_full.import_module(u'a')
                importlib_full.import_module(u'a.b')
                module = importlib_full.import_module(u'..c', u'a.b')
                self.assertEqual(module.__name__, u'a.c')

    def test_absolute_import_with_package(self):
        # Test importing a module from a package with an absolute name with
        # the 'package' argument given.
        pkg_name = u'pkg'
        pkg_long_name = u'{0}.__init__'.format(pkg_name)
        name = u'{0}.mod'.format(pkg_name)
        with util.mock_modules(pkg_long_name, name) as mock:
            with util.import_state(meta_path=[mock]):
                importlib_full.import_module(pkg_name)
                module = importlib_full.import_module(name, pkg_name)
                self.assertEqual(module.__name__, name)

    def test_relative_import_wo_package(self):
        # Relative imports cannot happen without the 'package' argument being
        # set.
        with self.assertRaises(TypeError):
            importlib_full.import_module(u'.support')


def test_main():
    from test.test_support import run_unittest
    run_unittest(ImportModuleTests)


if __name__ == u'__main__':
    test_main()
