import importlib_full.test
import os


def test_suite():
    directory = os.path.dirname(__file__)
    return importlib_full.test.test_suite('importlib_full.test.builtin', directory)


if __name__ == '__main__':
    from test.support import run_unittest
    run_unittest(test_suite())
