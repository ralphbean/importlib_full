from ... import machinery
from .. import abc

import unittest


class FinderTests(abc.FinderTests):

    u"""Test finding frozen modules."""

    def find(self, name, path=None):
        finder = machinery.FrozenImporter
        return finder.find_module(name, path)

    def test_module(self):
        name = u'__hello__'
        loader = self.find(name)
        self.assertTrue(hasattr(loader, u'load_module'))

    def test_package(self):
        loader = self.find(u'__phello__')
        self.assertTrue(hasattr(loader, u'load_module'))

    def test_module_in_package(self):
        loader = self.find(u'__phello__.spam', [u'__phello__'])
        self.assertTrue(hasattr(loader, u'load_module'))

    def test_package_in_package(self):
        # No frozen package within another package to test with.
        pass

    def test_package_over_module(self):
        # No easy way to test.
        pass

    def test_failure(self):
        loader = self.find(u'<not real>')
        self.assertTrue(loader is None)


def test_main():
    from test.test_support import run_unittest
    run_unittest(FinderTests)


if __name__ == u'__main__':
    test_main()
