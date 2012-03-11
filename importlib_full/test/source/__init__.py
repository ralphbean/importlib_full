import importlib_full.test
import os.path
import unittest


def test_suite():
    directory = os.path.dirname(__file__)
    return importlib_full.test.test_suite(u'importlib_full.test.source', directory)


if __name__ == u'__main__':
    from test.test_support import run_unittest
    run_unittest(test_suite())
