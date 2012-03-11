from importlib_full import _bootstrap
from . import util

import collections
import imp
import sys
import unittest


class PathHookTests(unittest.TestCase):

    u"""Test the path hook for extension modules."""
    # XXX Should it only succeed for pre-existing directories?
    # XXX Should it only work for directories containing an extension module?

    def hook(self, entry):
        return _bootstrap._file_path_hook(entry)

    def test_success(self):
        # Path hook should handle a directory where a known extension module
        # exists.
        self.assertTrue(hasattr(self.hook(util.PATH), u'find_module'))


def test_main():
    from test.test_support import run_unittest
    run_unittest(PathHookTests)


if __name__ == u'__main__':
    test_main()
