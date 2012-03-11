u"""Run importlib_full's test suite.

Specifying the ``--builtin`` flag will run tests, where applicable, with
builtins.__import__ instead of importlib_full.__import__.

"""
import importlib_full
from importlib_full.test.import_ import util
import os.path
from test.test_support import run_unittest
import sys
import unittest


def test_main():
    if u'__pycache__' in __file__:
        parts = __file__.split(os.path.sep)
        start_dir = sep.join(parts[:-2])
    else:
        start_dir = os.path.dirname(__file__)
    top_dir = os.path.dirname(os.path.dirname(start_dir))
    test_loader = unittest.TestLoader()
    if u'--builtin' in sys.argv:
        util.using___import__ = True
    run_unittest(test_loader.discover(start_dir, top_level_dir=top_dir))


if __name__ == u'__main__':
    test_main()
