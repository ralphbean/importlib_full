from __future__ import with_statement
from importlib_full import machinery
import imp
import unittest
from .. import abc
from .. import util
from test.test_support import captured_stdout

class LoaderTests(abc.LoaderTests):

    def test_module(self):
        with util.uncache(u'__hello__'), captured_stdout() as stdout:
            module = machinery.FrozenImporter.load_module(u'__hello__')
            check = {u'__name__': u'__hello__', u'__file__': u'<frozen>',
                    u'__package__': u'', u'__loader__': machinery.FrozenImporter}
            for attr, value in check.items():
                self.assertEqual(getattr(module, attr), value)
            self.assertEqual(stdout.getvalue(), u'Hello world!\n')

    def test_package(self):
        with util.uncache(u'__phello__'),  captured_stdout() as stdout:
            module = machinery.FrozenImporter.load_module(u'__phello__')
            check = {u'__name__': u'__phello__', u'__file__': u'<frozen>',
                     u'__package__': u'__phello__', u'__path__': [u'__phello__'],
                     u'__loader__': machinery.FrozenImporter}
            for attr, value in check.items():
                attr_value = getattr(module, attr)
                self.assertEqual(attr_value, value,
                                 u"for __phello__.%s, %r != %r" %
                                 (attr, attr_value, value))
            self.assertEqual(stdout.getvalue(), u'Hello world!\n')

    def test_lacking_parent(self):
        with util.uncache(u'__phello__', u'__phello__.spam'), \
             captured_stdout() as stdout:
            module = machinery.FrozenImporter.load_module(u'__phello__.spam')
            check = {u'__name__': u'__phello__.spam', u'__file__': u'<frozen>',
                    u'__package__': u'__phello__',
                    u'__loader__': machinery.FrozenImporter}
            for attr, value in check.items():
                attr_value = getattr(module, attr)
                self.assertEqual(attr_value, value,
                                 u"for __phello__.spam.%s, %r != %r" %
                                 (attr, attr_value, value))
            self.assertEqual(stdout.getvalue(), u'Hello world!\n')

    def test_module_reuse(self):
        with util.uncache(u'__hello__'), captured_stdout() as stdout:
            module1 = machinery.FrozenImporter.load_module(u'__hello__')
            module2 = machinery.FrozenImporter.load_module(u'__hello__')
            self.assertTrue(module1 is module2)
            self.assertEqual(stdout.getvalue(),
                             u'Hello world!\nHello world!\n')

    def test_state_after_failure(self):
        # No way to trigger an error in a frozen module.
        pass

    def test_unloadable(self):
        assert machinery.FrozenImporter.find_module(u'_not_real') is None
        with self.assertRaises(ImportError):
            machinery.FrozenImporter.load_module(u'_not_real')


class InspectLoaderTests(unittest.TestCase):

    u"""Tests for the InspectLoader methods for FrozenImporter."""

    def test_get_code(self):
        # Make sure that the code object is good.
        name = u'__hello__'
        with captured_stdout() as stdout:
            code = machinery.FrozenImporter.get_code(name)
            mod = imp.new_module(name)
            exec(code, mod.__dict__)
            self.assertTrue(hasattr(mod, u'initialized'))
            self.assertEqual(stdout.getvalue(), u'Hello world!\n')

    def test_get_source(self):
        # Should always return None.
        result = machinery.FrozenImporter.get_source(u'__hello__')
        self.assertTrue(result is None)

    def test_is_package(self):
        # Should be able to tell what is a package.
        test_for = ((u'__hello__', False), (u'__phello__', True),
                    (u'__phello__.spam', False))
        for name, is_package in test_for:
            result = machinery.FrozenImporter.is_package(name)
            self.assertTrue(bool(result) == is_package)

    def test_failure(self):
        # Raise ImportError for modules that are not frozen.
        for meth_name in (u'get_code', u'get_source', u'is_package'):
            method = getattr(machinery.FrozenImporter, meth_name)
            with self.assertRaises(ImportError):
                method(u'importlib_full')


def test_main():
    from test.test_support import run_unittest
    run_unittest(LoaderTests, InspectLoaderTests)


if __name__ == u'__main__':
    test_main()
