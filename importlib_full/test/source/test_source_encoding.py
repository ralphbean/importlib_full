from __future__ import with_statement
from importlib_full import _bootstrap
from . import util as source_util

import codecs
import re
import sys
# Because sys.path gets essentially blanked, need to have unicodedata already
# imported for the parser to use.
import unicodedata
import unittest
from io import open


CODING_RE = re.compile(ur'coding[:=]\s*([-\w.]+)')


class EncodingTest(unittest.TestCase):

    u"""PEP 3120 makes UTF-8 the default encoding for source code
    [default encoding].

    PEP 263 specifies how that can change on a per-file basis. Either the first
    or second line can contain the encoding line [encoding first line]
    encoding second line]. If the file has the BOM marker it is considered UTF-8
    implicitly [BOM]. If any encoding is specified it must be UTF-8, else it is
    an error [BOM and utf-8][BOM conflict].

    """

    variable = u'\u00fc'
    character = u'\u00c9'
    source_line = u"{0} = '{1}'\n".format(variable, character)
    module_name = u'_temp'

    def run_test(self, source):
        with source_util.create_modules(self.module_name) as mapping:
            with open(mapping[self.module_name], u'wb') as file:
                file.write(source)
            loader = _bootstrap._SourceFileLoader(self.module_name,
                                       mapping[self.module_name])
            return loader.load_module(self.module_name)

    def create_source(self, encoding):
        encoding_line = u"# coding={0}".format(encoding)
        assert CODING_RE.search(encoding_line)
        source_lines = [encoding_line.encode(u'utf-8')]
        source_lines.append(self.source_line.encode(encoding))
        return '\n'.join(source_lines)

    def test_non_obvious_encoding(self):
        # Make sure that an encoding that has never been a standard one for
        # Python works.
        encoding_line = u"# coding=koi8-r"
        assert CODING_RE.search(encoding_line)
        source = u"{0}\na=42\n".format(encoding_line).encode(u"koi8-r")
        self.run_test(source)

    # [default encoding]
    def test_default_encoding(self):
        self.run_test(self.source_line.encode(u'utf-8'))

    # [encoding first line]
    def test_encoding_on_first_line(self):
        encoding = u'Latin-1'
        source = self.create_source(encoding)
        self.run_test(source)

    # [encoding second line]
    def test_encoding_on_second_line(self):
        source = "#/usr/bin/python\n" + self.create_source(u'Latin-1')
        self.run_test(source)

    # [BOM]
    def test_bom(self):
        self.run_test(codecs.BOM_UTF8 + self.source_line.encode(u'utf-8'))

    # [BOM and utf-8]
    def test_bom_and_utf_8(self):
        source = codecs.BOM_UTF8 + self.create_source(u'utf-8')
        self.run_test(source)

    # [BOM conflict]
    def test_bom_conflict(self):
        source = codecs.BOM_UTF8 + self.create_source(u'latin-1')
        with self.assertRaises(SyntaxError):
            self.run_test(source)


class LineEndingTest(unittest.TestCase):

    ur"""Source written with the three types of line endings (\n, \r\n, \r)
    need to be readable [cr][crlf][lf]."""

    def run_test(self, line_ending):
        module_name = u'_temp'
        source_lines = ["a = 42", "b = -13", '']
        source = line_ending.join(source_lines)
        with source_util.create_modules(module_name) as mapping:
            with open(mapping[module_name], u'wb') as file:
                file.write(source)
            loader = _bootstrap._SourceFileLoader(module_name,
                                                 mapping[module_name])
            return loader.load_module(module_name)

    # [cr]
    def test_cr(self):
        self.run_test('\r')

    # [crlf]
    def test_crlf(self):
        self.run_test('\r\n')

    # [lf]
    def test_lf(self):
        self.run_test('\n')


def test_main():
    from test.test_support import run_unittest
    run_unittest(EncodingTest, LineEndingTest)


if __name__ == u'__main__':
    test_main()
