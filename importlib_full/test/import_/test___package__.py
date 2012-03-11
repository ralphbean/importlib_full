u"""PEP 366 ("Main module explicit relative imports") specifies the
semantics for the __package__ attribute on modules. This attribute is
used, when available, to detect which package a module belongs to (instead
of using the typical __path__/__name__ test).

"""
from __future__ import with_statement
import unittest
from .. import util
from . import util as import_util


class Using__package__(unittest.TestCase):

    u"""Use of __package__ supercedes the use of __name__/__path__ to calculate
    what package a module belongs to. The basic algorithm is [__package__]::

      def resolve_name(name, package, level):
          level -= 1
          base = package.rsplit('.', level)[0]
          return '{0}.{1}'.format(base, name)

    But since there is no guarantee that __package__ has been set (or not been
    set to None [None]), there has to be a way to calculate the attribute's value
    [__name__]::

      def calc_package(caller_name, has___path__):
          if has__path__:
              return caller_name
          else:
              return caller_name.rsplit('.', 1)[0]

    Then the normal algorithm for relative name imports can proceed as if
    __package__ had been set.

    """

    def test_using___package__(self):
        # [__package__]
        with util.mock_modules(u'pkg.__init__', u'pkg.fake') as importer:
            with util.import_state(meta_path=[importer]):
                import_util.import_(u'pkg.fake')
                module = import_util.import_(u'',
                                            globals={u'__package__': u'pkg.fake'},
                                            fromlist=[u'attr'], level=2)
        self.assertEqual(module.__name__, u'pkg')

    def test_using___name__(self, package_as_None=False):
        # [__name__]
        globals_ = {u'__name__': u'pkg.fake', u'__path__': []}
        if package_as_None:
            globals_[u'__package__'] = None
        with util.mock_modules(u'pkg.__init__', u'pkg.fake') as importer:
            with util.import_state(meta_path=[importer]):
                import_util.import_(u'pkg.fake')
                module = import_util.import_(u'', globals= globals_,
                                                fromlist=[u'attr'], level=2)
            self.assertEqual(module.__name__, u'pkg')

    def test_None_as___package__(self):
        # [None]
        self.test_using___name__(package_as_None=True)

    def test_bad__package__(self):
        globals = {u'__package__': u'<not real>'}
        with self.assertRaises(SystemError):
            import_util.import_(u'', globals, {}, [u'relimport'], 1)

    def test_bunk__package__(self):
        globals = {u'__package__': 42}
        with self.assertRaises(ValueError):
            import_util.import_(u'', globals, {}, [u'relimport'], 1)


class Setting__package__(unittest.TestCase):

    u"""Because __package__ is a new feature, it is not always set by a loader.
    Import will set it as needed to help with the transition to relying on
    __package__.

    For a top-level module, __package__ is set to None [top-level]. For a
    package __name__ is used for __package__ [package]. For submodules the
    value is __name__.rsplit('.', 1)[0] [submodule].

    """

    # [top-level]
    def test_top_level(self):
        with util.mock_modules(u'top_level') as mock:
            with util.import_state(meta_path=[mock]):
                del mock[u'top_level'].__package__
                module = import_util.import_(u'top_level')
                self.assertEqual(module.__package__, u'')

    # [package]
    def test_package(self):
        with util.mock_modules(u'pkg.__init__') as mock:
            with util.import_state(meta_path=[mock]):
                del mock[u'pkg'].__package__
                module = import_util.import_(u'pkg')
                self.assertEqual(module.__package__, u'pkg')

    # [submodule]
    def test_submodule(self):
        with util.mock_modules(u'pkg.__init__', u'pkg.mod') as mock:
            with util.import_state(meta_path=[mock]):
                del mock[u'pkg.mod'].__package__
                pkg = import_util.import_(u'pkg.mod')
                module = getattr(pkg, u'mod')
                self.assertEqual(module.__package__, u'pkg')


Setting__package__ = import_util.importlib_full_only(Setting__package__)
def test_main():
    from test.test_support import run_unittest
    run_unittest(Using__package__, Setting__package__)


if __name__ == u'__main__':
    test_main()
