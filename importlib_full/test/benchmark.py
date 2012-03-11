u"""Benchmark some basic import use-cases.

The assumption is made that this benchmark is run in a fresh interpreter and
thus has no external changes made to import-related attributes in sys.

"""
from __future__ import with_statement
from . import util
from .source import util as source_util
import decimal
import imp
import importlib_full
import os
import py_compile
import sys
import timeit


def bench(name, cleanup=lambda: None, **_3to2kwargs):
    if 'repeat' in _3to2kwargs: repeat = _3to2kwargs['repeat']; del _3to2kwargs['repeat']
    else: repeat = 3
    if 'seconds' in _3to2kwargs: seconds = _3to2kwargs['seconds']; del _3to2kwargs['seconds']
    else: seconds = 1
    u"""Bench the given statement as many times as necessary until total
    executions take one second."""
    stmt = u"__import__({!r})".format(name)
    timer = timeit.Timer(stmt)
    for x in xrange(repeat):
        total_time = 0
        count = 0
        while total_time < seconds:
            try:
                total_time += timer.timeit(1)
            finally:
                cleanup()
            count += 1
        else:
            # One execution too far
            if total_time > seconds:
                count -= 1
        yield count // seconds

def from_cache(seconds, repeat):
    u"""sys.modules"""
    name = u'<benchmark import>'
    module = imp.new_module(name)
    module.__file__ = u'<test>'
    module.__package__ = u''
    with util.uncache(name):
        sys.modules[name] = module
        for result in bench(name, repeat=repeat, seconds=seconds):
            yield result


def builtin_mod(seconds, repeat):
    u"""Built-in module"""
    name = u'errno'
    if name in sys.modules:
        del sys.modules[name]
    # Relying on built-in importer being implicit.
    for result in bench(name, lambda: sys.modules.pop(name), repeat=repeat,
                        seconds=seconds):
        yield result


def source_wo_bytecode(seconds, repeat):
    u"""Source w/o bytecode: simple"""
    sys.dont_write_bytecode = True
    try:
        name = u'__importlib_full_test_benchmark__'
        # Clears out sys.modules and puts an entry at the front of sys.path.
        with source_util.create_modules(name) as mapping:
            assert not os.path.exists(imp.cache_from_source(mapping[name]))
            for result in bench(name, lambda: sys.modules.pop(name), repeat=repeat,
                                seconds=seconds):
                yield result
    finally:
        sys.dont_write_bytecode = False


def decimal_wo_bytecode(seconds, repeat):
    u"""Source w/o bytecode: decimal"""
    name = u'decimal'
    decimal_bytecode = imp.cache_from_source(decimal.__file__)
    if os.path.exists(decimal_bytecode):
        os.unlink(decimal_bytecode)
    sys.dont_write_bytecode = True
    try:
        for result in bench(name, lambda: sys.modules.pop(name), repeat=repeat,
                            seconds=seconds):
            yield result
    finally:
        sys.dont_write_bytecode = False


def source_writing_bytecode(seconds, repeat):
    u"""Source writing bytecode: simple"""
    assert not sys.dont_write_bytecode
    name = u'__importlib_full_test_benchmark__'
    with source_util.create_modules(name) as mapping:
        def cleanup():
            sys.modules.pop(name)
            os.unlink(imp.cache_from_source(mapping[name]))
        for result in bench(name, cleanup, repeat=repeat, seconds=seconds):
            assert not os.path.exists(imp.cache_from_source(mapping[name]))
            yield result


def decimal_writing_bytecode(seconds, repeat):
    u"""Source writing bytecode: decimal"""
    assert not sys.dont_write_bytecode
    name = u'decimal'
    def cleanup():
        sys.modules.pop(name)
        os.unlink(imp.cache_from_source(decimal.__file__))
    for result in bench(name, cleanup, repeat=repeat, seconds=seconds):
        yield result


def source_using_bytecode(seconds, repeat):
    u"""Bytecode w/ source: simple"""
    name = u'__importlib_full_test_benchmark__'
    with source_util.create_modules(name) as mapping:
        py_compile.compile(mapping[name])
        assert os.path.exists(imp.cache_from_source(mapping[name]))
        for result in bench(name, lambda: sys.modules.pop(name), repeat=repeat,
                            seconds=seconds):
            yield result


def decimal_using_bytecode(seconds, repeat):
    u"""Bytecode w/ source: decimal"""
    name = u'decimal'
    py_compile.compile(decimal.__file__)
    for result in bench(name, lambda: sys.modules.pop(name), repeat=repeat,
                        seconds=seconds):
        yield result


def main(import_):
    __builtins__.__import__ = import_
    benchmarks = (from_cache, builtin_mod,
                  source_using_bytecode, source_wo_bytecode,
                  source_writing_bytecode,
                  decimal_using_bytecode, decimal_writing_bytecode,
                  decimal_wo_bytecode,)
    seconds = 1
    seconds_plural = u's' if seconds > 1 else u''
    repeat = 3
    header = u"Measuring imports/second over {} second{}, best out of {}\n"
    print header.format(seconds, seconds_plural, repeat)
    for benchmark in benchmarks:
        print benchmark.__doc__, u"[",
        sys.stdout.flush()
        results = []
        for result in benchmark(seconds=seconds, repeat=repeat):
            results.append(result)
            print result,
            sys.stdout.flush()
        assert not sys.dont_write_bytecode
        print u"]", u"best is", format(max(results), u',d')


if __name__ == u'__main__':
    import optparse

    parser = optparse.OptionParser()
    parser.add_option(u'-b', u'--builtin', dest=u'builtin', action=u'store_true',
                        default=False, help=u"use the built-in __import__")
    options, args = parser.parse_args()
    if args:
        raise RuntimeError(u"unrecognized args: {}".format(args))
    import_ = __import__
    if not options.builtin:
        import_ = importlib_full.__import__

    main(import_)
