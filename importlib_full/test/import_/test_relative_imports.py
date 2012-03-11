u"""Test relative imports (PEP 328)."""
from __future__ import with_statement
from .. import util
from . import util as import_util
import sys
import unittest

class RelativeImports(unittest.TestCase):

    u"""PEP 328 introduced relative imports. This allows for imports to occur
    from within a package without having to specify the actual package name.

    A simple example is to import another module within the same package
    [module from module]::

      # From pkg.mod1 with pkg.mod2 being a module.
      from . import mod2

    This also works for getting an attribute from a module that is specified
    in a relative fashion [attr from module]::

      # From pkg.mod1.
      from .mod2 import attr

    But this is in no way restricted to working between modules; it works
    from [package to module],::

      # From pkg, importing pkg.module which is a module.
      from . import module

    [module to package],::

      # Pull attr from pkg, called from pkg.module which is a module.
      from . import attr

    and [package to package]::

      # From pkg.subpkg1 (both pkg.subpkg[1,2] are packages).
      from .. import subpkg2

    The number of dots used is in no way restricted [deep import]::

      # Import pkg.attr from pkg.pkg1.pkg2.pkg3.pkg4.pkg5.
      from ...... import attr

    To prevent someone from accessing code that is outside of a package, one
    cannot reach the location containing the root package itself::

      # From pkg.__init__ [too high from package]
      from .. import top_level

      # From pkg.module [too high from module]
      from .. import top_level

     Relative imports are the only type of import that allow for an empty
     module name for an import [empty name].

    """

    def relative_import_test(self, create, globals_, callback):
        u"""Abstract out boilerplace for setting up for an import test."""
        uncache_names = []
        for name in create:
            if not name.endswith(u'.__init__'):
                uncache_names.append(name)
            else:
                uncache_names.append(name[:-len(u'.__init__')])
        with util.mock_modules(*create) as importer:
            with util.import_state(meta_path=[importer]):
                for global_ in globals_:
                    with util.uncache(*uncache_names):
                        callback(global_)


    def test_module_from_module(self):
        # [module from module]
        create = u'pkg.__init__', u'pkg.mod2'
        globals_ = {u'__package__': u'pkg'}, {u'__name__': u'pkg.mod1'}
        def callback(global_):
            import_util.import_(u'pkg')  # For __import__().
            module = import_util.import_(u'', global_, fromlist=[u'mod2'], level=1)
            self.assertEqual(module.__name__, u'pkg')
            self.assertTrue(hasattr(module, u'mod2'))
            self.assertEqual(module.mod2.attr, u'pkg.mod2')
        self.relative_import_test(create, globals_, callback)

    def test_attr_from_module(self):
        # [attr from module]
        create = u'pkg.__init__', u'pkg.mod2'
        globals_ = {u'__package__': u'pkg'}, {u'__name__': u'pkg.mod1'}
        def callback(global_):
            import_util.import_(u'pkg')  # For __import__().
            module = import_util.import_(u'mod2', global_, fromlist=[u'attr'],
                                            level=1)
            self.assertEqual(module.__name__, u'pkg.mod2')
            self.assertEqual(module.attr, u'pkg.mod2')
        self.relative_import_test(create, globals_, callback)

    def test_package_to_module(self):
        # [package to module]
        create = u'pkg.__init__', u'pkg.module'
        globals_ = ({u'__package__': u'pkg'},
                    {u'__name__': u'pkg', u'__path__': [u'blah']})
        def callback(global_):
            import_util.import_(u'pkg')  # For __import__().
            module = import_util.import_(u'', global_, fromlist=[u'module'],
                             level=1)
            self.assertEqual(module.__name__, u'pkg')
            self.assertTrue(hasattr(module, u'module'))
            self.assertEqual(module.module.attr, u'pkg.module')
        self.relative_import_test(create, globals_, callback)

    def test_module_to_package(self):
        # [module to package]
        create = u'pkg.__init__', u'pkg.module'
        globals_ = {u'__package__': u'pkg'}, {u'__name__': u'pkg.module'}
        def callback(global_):
            import_util.import_(u'pkg')  # For __import__().
            module = import_util.import_(u'', global_, fromlist=[u'attr'], level=1)
            self.assertEqual(module.__name__, u'pkg')
        self.relative_import_test(create, globals_, callback)

    def test_package_to_package(self):
        # [package to package]
        create = (u'pkg.__init__', u'pkg.subpkg1.__init__',
                    u'pkg.subpkg2.__init__')
        globals_ =  ({u'__package__': u'pkg.subpkg1'},
                     {u'__name__': u'pkg.subpkg1', u'__path__': [u'blah']})
        def callback(global_):
            module = import_util.import_(u'', global_, fromlist=[u'subpkg2'],
                                            level=2)
            self.assertEqual(module.__name__, u'pkg')
            self.assertTrue(hasattr(module, u'subpkg2'))
            self.assertEqual(module.subpkg2.attr, u'pkg.subpkg2.__init__')

    def test_deep_import(self):
        # [deep import]
        create = [u'pkg.__init__']
        for count in xrange(1,6):
            create.append(u'{0}.pkg{1}.__init__'.format(
                            create[-1][:-len(u'.__init__')], count))
        globals_ = ({u'__package__': u'pkg.pkg1.pkg2.pkg3.pkg4.pkg5'},
                    {u'__name__': u'pkg.pkg1.pkg2.pkg3.pkg4.pkg5',
                        u'__path__': [u'blah']})
        def callback(global_):
            import_util.import_(globals_[0][u'__package__'])
            module = import_util.import_(u'', global_, fromlist=[u'attr'], level=6)
            self.assertEqual(module.__name__, u'pkg')
        self.relative_import_test(create, globals_, callback)

    def test_too_high_from_package(self):
        # [too high from package]
        create = [u'top_level', u'pkg.__init__']
        globals_ = ({u'__package__': u'pkg'},
                    {u'__name__': u'pkg', u'__path__': [u'blah']})
        def callback(global_):
            import_util.import_(u'pkg')
            with self.assertRaises(ValueError):
                import_util.import_(u'', global_, fromlist=[u'top_level'],
                                    level=2)
        self.relative_import_test(create, globals_, callback)

    def test_too_high_from_module(self):
        # [too high from module]
        create = [u'top_level', u'pkg.__init__', u'pkg.module']
        globals_ = {u'__package__': u'pkg'}, {u'__name__': u'pkg.module'}
        def callback(global_):
            import_util.import_(u'pkg')
            with self.assertRaises(ValueError):
                import_util.import_(u'', global_, fromlist=[u'top_level'],
                                    level=2)
        self.relative_import_test(create, globals_, callback)

    def test_empty_name_w_level_0(self):
        # [empty name]
        with self.assertRaises(ValueError):
            import_util.import_(u'')

    def test_import_from_different_package(self):
        # Test importing from a different package than the caller.
        # in pkg.subpkg1.mod
        # from ..subpkg2 import mod
        create = [u'__runpy_pkg__.__init__',
                    u'__runpy_pkg__.__runpy_pkg__.__init__',
                    u'__runpy_pkg__.uncle.__init__',
                    u'__runpy_pkg__.uncle.cousin.__init__',
                    u'__runpy_pkg__.uncle.cousin.nephew']
        globals_ = {u'__package__': u'__runpy_pkg__.__runpy_pkg__'}
        def callback(global_):
            import_util.import_(u'__runpy_pkg__.__runpy_pkg__')
            module = import_util.import_(u'uncle.cousin', globals_, {},
                                    fromlist=[u'nephew'],
                                level=2)
            self.assertEqual(module.__name__, u'__runpy_pkg__.uncle.cousin')
        self.relative_import_test(create, globals_, callback)



def test_main():
    from test.test_support import run_unittest
    run_unittest(RelativeImports)

if __name__ == u'__main__':
    test_main()
