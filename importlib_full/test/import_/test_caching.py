u"""Test that sys.modules is used properly by import."""
from __future__ import with_statement
from .. import util
from . import util as import_util
import sys
from types import MethodType
import unittest


class UseCache(unittest.TestCase):

    u"""When it comes to sys.modules, import prefers it over anything else.

    Once a name has been resolved, sys.modules is checked to see if it contains
    the module desired. If so, then it is returned [use cache]. If it is not
    found, then the proper steps are taken to perform the import, but
    sys.modules is still used to return the imported module (e.g., not what a
    loader returns) [from cache on return]. This also applies to imports of
    things contained within a package and thus get assigned as an attribute
    [from cache to attribute] or pulled in thanks to a fromlist import
    [from cache for fromlist]. But if sys.modules contains None then
    ImportError is raised [None in cache].

    """
    def test_using_cache(self):
        # [use cache]
        module_to_use = u"some module found!"
        with util.uncache(module_to_use):
            sys.modules[u'some_module'] = module_to_use
            module = import_util.import_(u'some_module')
            self.assertEqual(id(module_to_use), id(module))

    def test_None_in_cache(self):
        #[None in cache]
        name = u'using_None'
        with util.uncache(name):
            sys.modules[name] = None
            with self.assertRaises(ImportError):
                import_util.import_(name)

    def create_mock(self, *names, **_3to2kwargs):
        if 'return_' in _3to2kwargs: return_ = _3to2kwargs['return_']; del _3to2kwargs['return_']
        else: return_ = None
        mock = util.mock_modules(*names)
        original_load = mock.load_module
        def load_module(self, fullname):
            original_load(fullname)
            return return_
        mock.load_module = MethodType(load_module, mock)
        return mock

    # __import__ inconsistent between loaders and built-in import when it comes
    #   to when to use the module in sys.modules and when not to.
    @import_util.importlib_full_only
    def test_using_cache_after_loader(self):
        # [from cache on return]
        with self.create_mock(u'module') as mock:
            with util.import_state(meta_path=[mock]):
                module = import_util.import_(u'module')
                self.assertEqual(id(module), id(sys.modules[u'module']))

    # See test_using_cache_after_loader() for reasoning.
    @import_util.importlib_full_only
    def test_using_cache_for_assigning_to_attribute(self):
        # [from cache to attribute]
        with self.create_mock(u'pkg.__init__', u'pkg.module') as importer:
            with util.import_state(meta_path=[importer]):
                module = import_util.import_(u'pkg.module')
                self.assertTrue(hasattr(module, u'module'))
                self.assertTrue(id(module.module), id(sys.modules[u'pkg.module']))

    # See test_using_cache_after_loader() for reasoning.
    @import_util.importlib_full_only
    def test_using_cache_for_fromlist(self):
        # [from cache for fromlist]
        with self.create_mock(u'pkg.__init__', u'pkg.module') as importer:
            with util.import_state(meta_path=[importer]):
                module = import_util.import_(u'pkg', fromlist=[u'module'])
                self.assertTrue(hasattr(module, u'module'))
                self.assertEqual(id(module.module),
                                 id(sys.modules[u'pkg.module']))


def test_main():
    from test.test_support import run_unittest
    run_unittest(UseCache)

if __name__ == u'__main__':
    test_main()
