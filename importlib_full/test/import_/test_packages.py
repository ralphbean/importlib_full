from __future__ import with_statement
from .. import util
from . import util as import_util
import sys
import unittest
import importlib_full


class ParentModuleTests(unittest.TestCase):

    u"""Importing a submodule should import the parent modules."""

    def test_import_parent(self):
        with util.mock_modules(u'pkg.__init__', u'pkg.module') as mock:
            with util.import_state(meta_path=[mock]):
                module = import_util.import_(u'pkg.module')
                self.assertTrue(u'pkg' in sys.modules)

    def test_bad_parent(self):
        with util.mock_modules(u'pkg.module') as mock:
            with util.import_state(meta_path=[mock]):
                with self.assertRaises(ImportError):
                    import_util.import_(u'pkg.module')

    def test_module_not_package(self):
        # Try to import a submodule from a non-package should raise ImportError.
        assert not hasattr(sys, u'__path__')
        with self.assertRaises(ImportError):
            import_util.import_(u'sys.no_submodules_here')


def test_main():
    from test.test_support import run_unittest
    run_unittest(ParentModuleTests)


if __name__ == u'__main__':
    test_main()
