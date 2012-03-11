from __future__ import with_statement
import importlib_full
from importlib_full import _bootstrap
from .. import abc
from .. import util
from . import util as source_util

import imp
import marshal
import os
import py_compile
import shutil
import stat
import sys
import unittest

from test.test_support import make_legacy_pyc
from io import open


class SimpleTest(unittest.TestCase):

    u"""Should have no issue importing a source module [basic]. And if there is
    a syntax error, it should raise a SyntaxError [syntax error].

    """

    # [basic]
    def test_module(self):
        with source_util.create_modules(u'_temp') as mapping:
            loader = _bootstrap._SourceFileLoader(u'_temp', mapping[u'_temp'])
            module = loader.load_module(u'_temp')
            self.assertTrue(u'_temp' in sys.modules)
            check = {u'__name__': u'_temp', u'__file__': mapping[u'_temp'],
                     u'__package__': u''}
            for attr, value in check.items():
                self.assertEqual(getattr(module, attr), value)

    def test_package(self):
        with source_util.create_modules(u'_pkg.__init__') as mapping:
            loader = _bootstrap._SourceFileLoader(u'_pkg',
                                                 mapping[u'_pkg.__init__'])
            module = loader.load_module(u'_pkg')
            self.assertTrue(u'_pkg' in sys.modules)
            check = {u'__name__': u'_pkg', u'__file__': mapping[u'_pkg.__init__'],
                     u'__path__': [os.path.dirname(mapping[u'_pkg.__init__'])],
                     u'__package__': u'_pkg'}
            for attr, value in check.items():
                self.assertEqual(getattr(module, attr), value)


    def test_lacking_parent(self):
        with source_util.create_modules(u'_pkg.__init__', u'_pkg.mod')as mapping:
            loader = _bootstrap._SourceFileLoader(u'_pkg.mod',
                                                    mapping[u'_pkg.mod'])
            module = loader.load_module(u'_pkg.mod')
            self.assertTrue(u'_pkg.mod' in sys.modules)
            check = {u'__name__': u'_pkg.mod', u'__file__': mapping[u'_pkg.mod'],
                     u'__package__': u'_pkg'}
            for attr, value in check.items():
                self.assertEqual(getattr(module, attr), value)

    def fake_mtime(self, fxn):
        u"""Fake mtime to always be higher than expected."""
        return lambda name: fxn(name) + 1

    def test_module_reuse(self):
        with source_util.create_modules(u'_temp') as mapping:
            loader = _bootstrap._SourceFileLoader(u'_temp', mapping[u'_temp'])
            module = loader.load_module(u'_temp')
            module_id = id(module)
            module_dict_id = id(module.__dict__)
            with open(mapping[u'_temp'], u'w') as file:
                file.write(u"testing_var = 42\n")
            # For filesystems where the mtime is only to a second granularity,
            # everything that has happened above can be too fast;
            # force an mtime on the source that is guaranteed to be different
            # than the original mtime.
            loader.path_mtime = self.fake_mtime(loader.path_mtime)
            module = loader.load_module(u'_temp')
            self.assertTrue(u'testing_var' in module.__dict__,
                         u"'testing_var' not in "
                            u"{0}".format(list(module.__dict__.keys())))
            self.assertEqual(module, sys.modules[u'_temp'])
            self.assertEqual(id(module), module_id)
            self.assertEqual(id(module.__dict__), module_dict_id)

    def test_state_after_failure(self):
        # A failed reload should leave the original module intact.
        attributes = (u'__file__', u'__path__', u'__package__')
        value = u'<test>'
        name = u'_temp'
        with source_util.create_modules(name) as mapping:
            orig_module = imp.new_module(name)
            for attr in attributes:
                setattr(orig_module, attr, value)
            with open(mapping[name], u'w') as file:
                file.write(u'+++ bad syntax +++')
            loader = _bootstrap._SourceFileLoader(u'_temp', mapping[u'_temp'])
            with self.assertRaises(SyntaxError):
                loader.load_module(name)
            for attr in attributes:
                self.assertEqual(getattr(orig_module, attr), value)

    # [syntax error]
    def test_bad_syntax(self):
        with source_util.create_modules(u'_temp') as mapping:
            with open(mapping[u'_temp'], u'w') as file:
                file.write(u'=')
            loader = _bootstrap._SourceFileLoader(u'_temp', mapping[u'_temp'])
            with self.assertRaises(SyntaxError):
                loader.load_module(u'_temp')
            self.assertTrue(u'_temp' not in sys.modules)

    def test_file_from_empty_string_dir(self):
        # Loading a module found from an empty string entry on sys.path should
        # not only work, but keep all attributes relative.
        file_path = u'_temp.py'
        with open(file_path, u'w') as file:
            file.write(u"# test file for importlib_full")
        try:
            with util.uncache(u'_temp'):
                loader = _bootstrap._SourceFileLoader(u'_temp', file_path)
                mod = loader.load_module(u'_temp')
                self.assertEqual(file_path, mod.__file__)
                self.assertEqual(imp.cache_from_source(file_path),
                                 mod.__cached__)
        finally:
            os.unlink(file_path)
            pycache = os.path.dirname(imp.cache_from_source(file_path))
            shutil.rmtree(pycache)


class BadBytecodeTest(unittest.TestCase):

    def import_(self, file, module_name):
        loader = self.loader(module_name, file)
        module = loader.load_module(module_name)
        self.assertTrue(module_name in sys.modules)

    def manipulate_bytecode(self, name, mapping, manipulator, **_3to2kwargs):
        if 'del_source' in _3to2kwargs: del_source = _3to2kwargs['del_source']; del _3to2kwargs['del_source']
        else: del_source = False
        u"""Manipulate the bytecode of a module by passing it into a callable
        that returns what to use as the new bytecode."""
        try:
            del sys.modules[u'_temp']
        except KeyError:
            pass
        py_compile.compile(mapping[name])
        if not del_source:
            bytecode_path = imp.cache_from_source(mapping[name])
        else:
            os.unlink(mapping[name])
            bytecode_path = make_legacy_pyc(mapping[name])
        if manipulator:
            with open(bytecode_path, u'rb') as file:
                bc = file.read()
                new_bc = manipulator(bc)
            with open(bytecode_path, u'wb') as file:
                if new_bc is not None:
                    file.write(new_bc)
        return bytecode_path

    def _test_empty_file(self, test, **_3to2kwargs):
        if 'del_source' in _3to2kwargs: del_source = _3to2kwargs['del_source']; del _3to2kwargs['del_source']
        else: del_source = False
        with source_util.create_modules(u'_temp') as mapping:
            bc_path = self.manipulate_bytecode(u'_temp', mapping,
                                                lambda bc: '',
                                                del_source=del_source)
            test(u'_temp', mapping, bc_path)

    @source_util.writes_bytecode_files
    def _test_partial_magic(self, test, **_3to2kwargs):
        # When their are less than 4 bytes to a .pyc, regenerate it if
        # possible, else raise ImportError.
        if 'del_source' in _3to2kwargs: del_source = _3to2kwargs['del_source']; del _3to2kwargs['del_source']
        else: del_source = False
        with source_util.create_modules(u'_temp') as mapping:
            bc_path = self.manipulate_bytecode(u'_temp', mapping,
                                                lambda bc: bc[:3],
                                                del_source=del_source)
            test(u'_temp', mapping, bc_path)

    def _test_magic_only(self, test, **_3to2kwargs):
        if 'del_source' in _3to2kwargs: del_source = _3to2kwargs['del_source']; del _3to2kwargs['del_source']
        else: del_source = False
        with source_util.create_modules(u'_temp') as mapping:
            bc_path = self.manipulate_bytecode(u'_temp', mapping,
                                                lambda bc: bc[:4],
                                                del_source=del_source)
            test(u'_temp', mapping, bc_path)

    def _test_partial_timestamp(self, test, **_3to2kwargs):
        if 'del_source' in _3to2kwargs: del_source = _3to2kwargs['del_source']; del _3to2kwargs['del_source']
        else: del_source = False
        with source_util.create_modules(u'_temp') as mapping:
            bc_path = self.manipulate_bytecode(u'_temp', mapping,
                                                lambda bc: bc[:7],
                                                del_source=del_source)
            test(u'_temp', mapping, bc_path)

    def _test_no_marshal(self, **_3to2kwargs):
        if 'del_source' in _3to2kwargs: del_source = _3to2kwargs['del_source']; del _3to2kwargs['del_source']
        else: del_source = False
        with source_util.create_modules(u'_temp') as mapping:
            bc_path = self.manipulate_bytecode(u'_temp', mapping,
                                                lambda bc: bc[:8],
                                                del_source=del_source)
            file_path = mapping[u'_temp'] if not del_source else bc_path
            with self.assertRaises(EOFError):
                self.import_(file_path, u'_temp')

    def _test_non_code_marshal(self, **_3to2kwargs):
        if 'del_source' in _3to2kwargs: del_source = _3to2kwargs['del_source']; del _3to2kwargs['del_source']
        else: del_source = False
        with source_util.create_modules(u'_temp') as mapping:
            bytecode_path = self.manipulate_bytecode(u'_temp', mapping,
                                    lambda bc: bc[:8] + marshal.dumps('abcd'),
                                    del_source=del_source)
            file_path = mapping[u'_temp'] if not del_source else bytecode_path
            with self.assertRaises(ImportError):
                self.import_(file_path, u'_temp')

    def _test_bad_marshal(self, **_3to2kwargs):
        if 'del_source' in _3to2kwargs: del_source = _3to2kwargs['del_source']; del _3to2kwargs['del_source']
        else: del_source = False
        with source_util.create_modules(u'_temp') as mapping:
            bytecode_path = self.manipulate_bytecode(u'_temp', mapping,
                                                lambda bc: bc[:8] + '<test>',
                                                del_source=del_source)
            file_path = mapping[u'_temp'] if not del_source else bytecode_path
            with self.assertRaises(EOFError):
                self.import_(file_path, u'_temp')

    def _test_bad_magic(self, test, **_3to2kwargs):
        if 'del_source' in _3to2kwargs: del_source = _3to2kwargs['del_source']; del _3to2kwargs['del_source']
        else: del_source = False
        with source_util.create_modules(u'_temp') as mapping:
            bc_path = self.manipulate_bytecode(u'_temp', mapping,
                                    lambda bc: '\x00\x00\x00\x00' + bc[4:])
            test(u'_temp', mapping, bc_path)


class SourceLoaderBadBytecodeTest(BadBytecodeTest):

    loader = _bootstrap._SourceFileLoader

    @source_util.writes_bytecode_files
    def test_empty_file(self):
        # When a .pyc is empty, regenerate it if possible, else raise
        # ImportError.
        def test(name, mapping, bytecode_path):
            self.import_(mapping[name], name)
            with open(bytecode_path, u'rb') as file:
                self.assertGreater(len(file.read()), 8)

        self._test_empty_file(test)

    def test_partial_magic(self):
        def test(name, mapping, bytecode_path):
            self.import_(mapping[name], name)
            with open(bytecode_path, u'rb') as file:
                self.assertGreater(len(file.read()), 8)

        self._test_partial_magic(test)

    @source_util.writes_bytecode_files
    def test_magic_only(self):
        # When there is only the magic number, regenerate the .pyc if possible,
        # else raise EOFError.
        def test(name, mapping, bytecode_path):
            self.import_(mapping[name], name)
            with open(bytecode_path, u'rb') as file:
                self.assertGreater(len(file.read()), 8)

    @source_util.writes_bytecode_files
    def test_bad_magic(self):
        # When the magic number is different, the bytecode should be
        # regenerated.
        def test(name, mapping, bytecode_path):
            self.import_(mapping[name], name)
            with open(bytecode_path, u'rb') as bytecode_file:
                self.assertEqual(bytecode_file.read(4), imp.get_magic())

        self._test_bad_magic(test)

    @source_util.writes_bytecode_files
    def test_partial_timestamp(self):
        # When the timestamp is partial, regenerate the .pyc, else
        # raise EOFError.
        def test(name, mapping, bc_path):
            self.import_(mapping[name], name)
            with open(bc_path, u'rb') as file:
                self.assertGreater(len(file.read()), 8)

    @source_util.writes_bytecode_files
    def test_no_marshal(self):
        # When there is only the magic number and timestamp, raise EOFError.
        self._test_no_marshal()

    @source_util.writes_bytecode_files
    def test_non_code_marshal(self):
        self._test_non_code_marshal()
        # XXX ImportError when sourceless

    # [bad marshal]
    @source_util.writes_bytecode_files
    def test_bad_marshal(self):
        # Bad marshal data should raise a ValueError.
        self._test_bad_marshal()

    # [bad timestamp]
    @source_util.writes_bytecode_files
    def test_old_timestamp(self):
        # When the timestamp is older than the source, bytecode should be
        # regenerated.
        zeros = '\x00\x00\x00\x00'
        with source_util.create_modules(u'_temp') as mapping:
            py_compile.compile(mapping[u'_temp'])
            bytecode_path = imp.cache_from_source(mapping[u'_temp'])
            with open(bytecode_path, u'r+b') as bytecode_file:
                bytecode_file.seek(4)
                bytecode_file.write(zeros)
            self.import_(mapping[u'_temp'], u'_temp')
            source_mtime = os.path.getmtime(mapping[u'_temp'])
            source_timestamp = importlib_full._w_long(source_mtime)
            with open(bytecode_path, u'rb') as bytecode_file:
                bytecode_file.seek(4)
                self.assertEqual(bytecode_file.read(4), source_timestamp)

    # [bytecode read-only]
    @source_util.writes_bytecode_files
    def test_read_only_bytecode(self):
        # When bytecode is read-only but should be rewritten, fail silently.
        with source_util.create_modules(u'_temp') as mapping:
            # Create bytecode that will need to be re-created.
            py_compile.compile(mapping[u'_temp'])
            bytecode_path = imp.cache_from_source(mapping[u'_temp'])
            with open(bytecode_path, u'r+b') as bytecode_file:
                bytecode_file.seek(0)
                bytecode_file.write('\x00\x00\x00\x00')
            # Make the bytecode read-only.
            os.chmod(bytecode_path,
                        stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            try:
                # Should not raise IOError!
                self.import_(mapping[u'_temp'], u'_temp')
            finally:
                # Make writable for eventual clean-up.
                os.chmod(bytecode_path, stat.S_IWUSR)


class SourcelessLoaderBadBytecodeTest(BadBytecodeTest):

    loader = _bootstrap._SourcelessFileLoader

    def test_empty_file(self):
        def test(name, mapping, bytecode_path):
            with self.assertRaises(ImportError):
                self.import_(bytecode_path, name)

        self._test_empty_file(test, del_source=True)

    def test_partial_magic(self):
        def test(name, mapping, bytecode_path):
            with self.assertRaises(ImportError):
                self.import_(bytecode_path, name)
        self._test_partial_magic(test, del_source=True)

    def test_magic_only(self):
        def test(name, mapping, bytecode_path):
            with self.assertRaises(EOFError):
                self.import_(bytecode_path, name)

        self._test_magic_only(test, del_source=True)

    def test_bad_magic(self):
        def test(name, mapping, bytecode_path):
            with self.assertRaises(ImportError):
                self.import_(bytecode_path, name)

        self._test_bad_magic(test, del_source=True)

    def test_partial_timestamp(self):
        def test(name, mapping, bytecode_path):
            with self.assertRaises(EOFError):
                self.import_(bytecode_path, name)

        self._test_partial_timestamp(test, del_source=True)

    def test_no_marshal(self):
        self._test_no_marshal(del_source=True)

    def test_non_code_marshal(self):
        self._test_non_code_marshal(del_source=True)


def test_main():
    from test.test_support import run_unittest
    run_unittest(SimpleTest,
                 SourceLoaderBadBytecodeTest,
                 SourcelessLoaderBadBytecodeTest
                )


if __name__ == u'__main__':
    test_main()
