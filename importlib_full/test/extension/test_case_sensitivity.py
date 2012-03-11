from __future__ import with_statement
import sys
from test import test_support as support
import unittest
from importlib_full import _bootstrap
from .. import util
from . import util as ext_util


class ExtensionModuleCaseSensitivityTest(unittest.TestCase):

    def find_module(self):
        good_name = ext_util.NAME
        bad_name = good_name.upper()
        assert good_name != bad_name
        finder = _bootstrap._FileFinder(ext_util.PATH,
                                        _bootstrap._ExtensionFinderDetails())
        return finder.find_module(bad_name)

    def test_case_sensitive(self):
        with support.EnvironmentVarGuard() as env:
            env.unset(u'PYTHONCASEOK')
            loader = self.find_module()
            self.assertIsNone(loader)

    def test_case_insensitivity(self):
        with support.EnvironmentVarGuard() as env:
            env.set(u'PYTHONCASEOK', u'1')
            loader = self.find_module()
            self.assertTrue(hasattr(loader, u'load_module'))




ExtensionModuleCaseSensitivityTest = util.case_insensitive_tests(ExtensionModuleCaseSensitivityTest)
def test_main():
    if ext_util.FILENAME is None:
        return
    support.run_unittest(ExtensionModuleCaseSensitivityTest)


if __name__ == u'__main__':
    test_main()
