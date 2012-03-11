from __future__ import with_statement
from importlib_full import _bootstrap
from . import util as ext_util
from .. import abc
from .. import util

import sys
import unittest


class LoaderTests(abc.LoaderTests):

    u"""Test load_module() for extension modules."""

    def load_module(self, fullname):
        loader = _bootstrap._ExtensionFileLoader(ext_util.NAME,
                                                ext_util.FILEPATH)
        return loader.load_module(fullname)

    def test_module(self):
        with util.uncache(ext_util.NAME):
            module = self.load_module(ext_util.NAME)
            for attr, value in [(u'__name__', ext_util.NAME),
                                (u'__file__', ext_util.FILEPATH),
                                (u'__package__', u'')]:
                self.assertEqual(getattr(module, attr), value)
            self.assertTrue(ext_util.NAME in sys.modules)
            self.assertTrue(isinstance(module.__loader__,
                                    _bootstrap._ExtensionFileLoader))

    def test_package(self):
        # Extensions are not found in packages.
        pass

    def test_lacking_parent(self):
        # Extensions are not found in packages.
        pass

    def test_module_reuse(self):
        with util.uncache(ext_util.NAME):
            module1 = self.load_module(ext_util.NAME)
            module2 = self.load_module(ext_util.NAME)
            self.assertTrue(module1 is module2)

    def test_state_after_failure(self):
        # No easy way to trigger a failure after a successful import.
        pass

    def test_unloadable(self):
        with self.assertRaises(ImportError):
            self.load_module(u'asdfjkl;')


def test_main():
    from test.test_support import run_unittest
    run_unittest(LoaderTests)


if __name__ == u'__main__':
    test_main()
