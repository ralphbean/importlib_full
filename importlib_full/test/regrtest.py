u"""Run Python's standard test suite using importlib_full.__import__.

Tests known to fail because of assumptions that importlib_full (properly)
invalidates are automatically skipped if the entire test suite is run.
Otherwise all command-line options valid for test.regrtest are also valid for
this script.

XXX FAILING
  * test_import
    - test_incorrect_code_name
        file name differing between __file__ and co_filename (r68360 on trunk)
    - test_import_by_filename
        exception for trying to import by file name does not match

"""
import importlib_full
import sys
from test import regrtest

if __name__ == u'__main__':
    __builtins__.__import__ = importlib_full.__import__

    exclude = [u'--exclude',
                u'test_frozen', # Does not expect __loader__ attribute
                u'test_pkg',  # Does not expect __loader__ attribute
                u'test_pydoc', # Does not expect __loader__ attribute
              ]

    # Switching on --exclude implies running all test but the ones listed, so
    # only use it when one is not running an explicit test
    if len(sys.argv) == 1:
        # No programmatic way to specify tests to exclude
        sys.argv.extend(exclude)

    regrtest.main(quiet=True, verbose2=True)
