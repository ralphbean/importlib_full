u"""Abstract base classes related to import."""
from __future__ import absolute_import
from . import _bootstrap
from . import machinery
from . import util
import abc
import imp
import io
import marshal
import os.path
import sys
import tokenize
import types
import warnings


class Loader():

    __metaclass__ = abc.ABCMeta
    u"""Abstract base class for import loaders."""

    @abc.abstractmethod
    def load_module(self, fullname):
        u"""Abstract method which when implemented should load a module.
        The fullname is a str."""
        raise NotImplementedError


class Finder():

    __metaclass__ = abc.ABCMeta
    u"""Abstract base class for import finders."""

    @abc.abstractmethod
    def find_module(self, fullname, path=None):
        u"""Abstract method which when implemented should find a module.
        The fullname is a str and the optional path is a str or None.
        Returns a Loader object.
        """
        raise NotImplementedError

Finder.register(machinery.BuiltinImporter)
Finder.register(machinery.FrozenImporter)
Finder.register(machinery.PathFinder)


class ResourceLoader(Loader):

    u"""Abstract base class for loaders which can return data from their
    back-end storage.

    This ABC represents one of the optional protocols specified by PEP 302.

    """

    @abc.abstractmethod
    def get_data(self, path):
        u"""Abstract method which when implemented should return the bytes for
        the specified path.  The path must be a str."""
        raise NotImplementedError


class InspectLoader(Loader):

    u"""Abstract base class for loaders which support inspection about the
    modules they can load.

    This ABC represents one of the optional protocols specified by PEP 302.

    """

    @abc.abstractmethod
    def is_package(self, fullname):
        u"""Abstract method which when implemented should return whether the
        module is a package.  The fullname is a str.  Returns a bool."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_code(self, fullname):
        u"""Abstract method which when implemented should return the code object
        for the module.  The fullname is a str.  Returns a types.CodeType."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_source(self, fullname):
        u"""Abstract method which should return the source code for the
        module.  The fullname is a str.  Returns a str."""
        raise NotImplementedError

InspectLoader.register(machinery.BuiltinImporter)
InspectLoader.register(machinery.FrozenImporter)


class ExecutionLoader(InspectLoader):

    u"""Abstract base class for loaders that wish to support the execution of
    modules as scripts.

    This ABC represents one of the optional protocols specified in PEP 302.

    """

    @abc.abstractmethod
    def get_filename(self, fullname):
        u"""Abstract method which should return the value that __file__ is to be
        set to."""
        raise NotImplementedError


class SourceLoader(_bootstrap.SourceLoader, ResourceLoader, ExecutionLoader):

    u"""Abstract base class for loading source code (and optionally any
    corresponding bytecode).

    To support loading from source code, the abstractmethods inherited from
    ResourceLoader and ExecutionLoader need to be implemented. To also support
    loading from bytecode, the optional methods specified directly by this ABC
    is required.

    Inherited abstractmethods not implemented in this ABC:

        * ResourceLoader.get_data
        * ExecutionLoader.get_filename

    """

    def path_mtime(self, path):
        u"""Return the (int) modification time for the path (str)."""
        raise NotImplementedError

    def set_data(self, path, data):
        u"""Write the bytes to the path (if possible).

        Accepts a str path and data as bytes.

        Any needed intermediary directories are to be created. If for some
        reason the file cannot be written because of permissions, fail
        silently.

        """
        raise NotImplementedError


class PyLoader(SourceLoader):

    u"""Implement the deprecated PyLoader ABC in terms of SourceLoader.

    This class has been deprecated! It is slated for removal in Python 3.4.
    If compatibility with Python 3.1 is not needed then implement the
    SourceLoader ABC instead of this class. If Python 3.1 compatibility is
    needed, then use the following idiom to have a single class that is
    compatible with Python 3.1 onwards::

        try:
            from importlib_full.abc import SourceLoader
        except ImportError:
            from importlib_full.abc import PyLoader as SourceLoader


        class CustomLoader(SourceLoader):
            def get_filename(self, fullname):
                # Implement ...

            def source_path(self, fullname):
                '''Implement source_path in terms of get_filename.'''
                try:
                    return self.get_filename(fullname)
                except ImportError:
                    return None

            def is_package(self, fullname):
                filename = os.path.basename(self.get_filename(fullname))
                return os.path.splitext(filename)[0] == '__init__'

    """

    @abc.abstractmethod
    def is_package(self, fullname):
        raise NotImplementedError

    @abc.abstractmethod
    def source_path(self, fullname):
        u"""Abstract method.  Accepts a str module name and returns the path to
        the source code for the module."""
        raise NotImplementedError

    def get_filename(self, fullname):
        u"""Implement get_filename in terms of source_path.

        As get_filename should only return a source file path there is no
        chance of the path not existing but loading still being possible, so
        ImportError should propagate instead of being turned into returning
        None.

        """
        warnings.warn(u"importlib_full.abc.PyLoader is deprecated and is "
                            u"slated for removal in Python 3.4; "
                            u"use SourceLoader instead. "
                            u"See the importlib_full documentation on how to be "
                            u"compatible with Python 3.1 onwards.",
                        PendingDeprecationWarning)
        path = self.source_path(fullname)
        if path is None:
            raise ImportError
        else:
            return path


class PyPycLoader(PyLoader):

    u"""Abstract base class to assist in loading source and bytecode by
    requiring only back-end storage methods to be implemented.

    This class has been deprecated! Removal is slated for Python 3.4. Implement
    the SourceLoader ABC instead. If Python 3.1 compatibility is needed, see
    PyLoader.

    The methods get_code, get_source, and load_module are implemented for the
    user.

    """

    def get_filename(self, fullname):
        u"""Return the source or bytecode file path."""
        path = self.source_path(fullname)
        if path is not None:
            return path
        path = self.bytecode_path(fullname)
        if path is not None:
            return path
        raise ImportError(u"no source or bytecode path available for "
                            u"%r" % fullname)

    def get_code(self, fullname):
        u"""Get a code object from source or bytecode."""
        warnings.warn(u"importlib_full.abc.PyPycLoader is deprecated and slated for "
                            u"removal in Python 3.4; use SourceLoader instead. "
                            u"If Python 3.1 compatibility is required, see the "
                            u"latest documentation for PyLoader.",
                        PendingDeprecationWarning)
        source_timestamp = self.source_mtime(fullname)
        # Try to use bytecode if it is available.
        bytecode_path = self.bytecode_path(fullname)
        if bytecode_path:
            data = self.get_data(bytecode_path)
            try:
                magic = data[:4]
                if len(magic) < 4:
                    raise ImportError(u"bad magic number in %s" % fullname)
                raw_timestamp = data[4:8]
                if len(raw_timestamp) < 4:
                    raise EOFError(u"bad timestamp in %s" % fullname)
                pyc_timestamp = marshal._r_long(raw_timestamp)
                bytecode = data[8:]
                # Verify that the magic number is valid.
                if imp.get_magic() != magic:
                    raise ImportError(u"bad magic number in %s" % fullname)
                # Verify that the bytecode is not stale (only matters when
                # there is source to fall back on.
                if source_timestamp:
                    if pyc_timestamp < source_timestamp:
                        raise ImportError(u"bytecode is stale")
            except (ImportError, EOFError):
                # If source is available give it a shot.
                if source_timestamp is not None:
                    pass
                else:
                    raise
            else:
                # Bytecode seems fine, so try to use it.
                return marshal.loads(bytecode)
        elif source_timestamp is None:
            raise ImportError(u"no source or bytecode available to create code "
                                u"object for %r" % fullname)
        # Use the source.
        source_path = self.source_path(fullname)
        if source_path is None:
            message = u"a source path must exist to load %s" % fullname
            raise ImportError(message)
        source = self.get_data(source_path)
        code_object = compile(source, source_path, u'exec', dont_inherit=True)
        # Generate bytecode and write it out.
        if not sys.dont_write_bytecode:
            data = bytearray(imp.get_magic())
            data.extend(marshal._w_long(source_timestamp))
            data.extend(marshal.dumps(code_object))
            self.write_bytecode(fullname, data)
        return code_object

    @abc.abstractmethod
    def source_mtime(self, fullname):
        u"""Abstract method. Accepts a str filename and returns an int
        modification time for the source of the module."""
        raise NotImplementedError

    @abc.abstractmethod
    def bytecode_path(self, fullname):
        u"""Abstract method. Accepts a str filename and returns the str pathname
        to the bytecode for the module."""
        raise NotImplementedError

    @abc.abstractmethod
    def write_bytecode(self, fullname, bytecode):
        u"""Abstract method.  Accepts a str filename and bytes object
        representing the bytecode for the module.  Returns a boolean
        representing whether the bytecode was written or not."""
        raise NotImplementedError
