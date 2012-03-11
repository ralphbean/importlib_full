from __future__ import with_statement
from importlib_full import _bootstrap
from . import util as source_util
import unittest


class PathHookTest(unittest.TestCase):

    u"""Test the path hook for source."""

    def test_success(self):
        with source_util.create_modules(u'dummy') as mapping:
            self.assertTrue(hasattr(_bootstrap._file_path_hook(mapping[u'.root']),
                                 u'find_module'))

    def test_empty_string(self):
        # The empty string represents the cwd.
        self.assertTrue(hasattr(_bootstrap._file_path_hook(u''), u'find_module'))


def test_main():
    from test.test_support import run_unittest
    run_unittest(PathHookTest)


if __name__ == u'__main__':
    test_main()
