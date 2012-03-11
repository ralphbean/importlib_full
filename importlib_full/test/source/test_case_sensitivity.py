u"""Test case-sensitivity (PEP 235)."""
from __future__ import with_statement
from importlib_full import _bootstrap
from .. import util
from . import util as source_util
import os
import sys
from test import test_support as test_support
import unittest


class CaseSensitivityTest(unittest.TestCase):

    u"""PEP 235 dictates that on case-preserving, case-insensitive file systems
    that imports are case-sensitive unless the PYTHONCASEOK environment
    variable is set."""

    name = u'MoDuLe'
    assert name != name.lower()

    def find(self, path):
        finder = _bootstrap._FileFinder(path,
                                        _bootstrap._SourceFinderDetails(),
                                        _bootstrap._SourcelessFinderDetails())
        return finder.find_module(self.name)

    def sensitivity_test(self):
        u"""Look for a module with matching and non-matching sensitivity."""
        sensitive_pkg = u'sensitive.{0}'.format(self.name)
        insensitive_pkg = u'insensitive.{0}'.format(self.name.lower())
        context = source_util.create_modules(insensitive_pkg, sensitive_pkg)
        with context as mapping:
            sensitive_path = os.path.join(mapping[u'.root'], u'sensitive')
            insensitive_path = os.path.join(mapping[u'.root'], u'insensitive')
            return self.find(sensitive_path), self.find(insensitive_path)

    def test_sensitive(self):
        with test_support.EnvironmentVarGuard() as env:
            env.unset(u'PYTHONCASEOK')
            sensitive, insensitive = self.sensitivity_test()
            self.assertTrue(hasattr(sensitive, u'load_module'))
            self.assertIn(self.name, sensitive.get_filename(self.name))
            self.assertIsNone(insensitive)

    def test_insensitive(self):
        with test_support.EnvironmentVarGuard() as env:
            env.set(u'PYTHONCASEOK', u'1')
            sensitive, insensitive = self.sensitivity_test()
            self.assertTrue(hasattr(sensitive, u'load_module'))
            self.assertIn(self.name, sensitive.get_filename(self.name))
            self.assertTrue(hasattr(insensitive, u'load_module'))
            self.assertIn(self.name, insensitive.get_filename(self.name))


CaseSensitivityTest = util.case_insensitive_tests(CaseSensitivityTest)
def test_main():
    test_support.run_unittest(CaseSensitivityTest)


if __name__ == u'__main__':
    test_main()
