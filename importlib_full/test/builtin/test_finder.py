from __future__ import with_statement
from importlib_full import machinery
from .. import abc
from .. import util
from . import util as builtin_util

import sys
import unittest

class FinderTests(abc.FinderTests):

    u"""Test find_module() for built-in modules."""

    def test_module(self):
        # Common case.
        with util.uncache(builtin_util.NAME):
            found = machinery.BuiltinImporter.find_module(builtin_util.NAME)
            self.assertTrue(found)

    def test_package(self):
        # Built-in modules cannot be a package.
        pass

    def test_module_in_package(self):
        # Built-in modules cannobt be in a package.
        pass

    def test_package_in_package(self):
        # Built-in modules cannot be a package.
        pass

    def test_package_over_module(self):
        # Built-in modules cannot be a package.
        pass

    def test_failure(self):
        assert u'importlib_full' not in sys.builtin_module_names
        loader = machinery.BuiltinImporter.find_module(u'importlib_full')
        self.assertTrue(loader is None)

    def test_ignore_path(self):
        # The value for 'path' should always trigger a failed import.
        with util.uncache(builtin_util.NAME):
            loader = machinery.BuiltinImporter.find_module(builtin_util.NAME,
                                                            [u'pkg'])
            self.assertTrue(loader is None)



def test_main():
    from test.test_support import run_unittest
    run_unittest(FinderTests)


if __name__ == u'__main__':
    test_main()
