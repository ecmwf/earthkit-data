# (C) Copyright 2020- ECMWF.  #
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import ABCMeta
from abc import abstractmethod


class Base(metaclass=ABCMeta):
    """Base class for all objects in earthkit.data."""

    pass


class Encodable(Base):
    """Base class for all objects that can be encoded using an encoder."""

    @abstractmethod
    def to_target(self, target, *args, **kwargs):
        pass

    @abstractmethod
    def _default_encoder(self):
        pass

    @abstractmethod
    def _encode(self, encoder, *, hints=None, **kwargs):
        """Double dispatch to the encoder"""
        pass


class Loader(Base):
    """Base class for all objects that can be loaded using a loader."""

    @abstractmethod
    def cache_file(self, *args, **kwargs):
        pass

    def mutate(self):
        # Give a chance to `directory` or `zip` to change the reader
        # Give a chance to `multi` to change source
        return self

    def mutate_source(self):
        # The source may ask if it needs to mutate
        return None

    def ignore(self):
        """Indicates to ignore this source in concatenation/merging.

        Returns
        -------
        bool
        """
        # Used by multi-source
        return False

    @abstractmethod
    def to_data_object(self):
        pass

    # def to_target(self, target, *args, **kwargs):
    #     from earthkit.data.targets import to_target

    #     to_target(target, *args, data=self, **kwargs)

    # def _encode(self, encoder, **kwargs):
    #     return encoder._encode(self, **kwargs)


class FileLoaderMixin:
    _format = None
    _binary = True
    _appendable = True

    def __init__(self, *args, **kwargs):
        print("FileLoaderMixin.__init__", self._format, self._default_encoder())

    def _default_encoder(self):
        print("FileLoaderMixin._default_encoder", self._format)
        return self._format

    def _encode(self, encoder, *args, **kwargs):
        result = self._encode_path(encoder, *args, **kwargs)
        if result is not None:
            return result
        return encoder._encode_default(self, *args, **kwargs)

    @abstractmethod
    def _encode_default(self, encoder, *args, **kwargs):
        pass

    def _encode_path(self, encoder, *args, **kwargs):
        path_info = self._path_info()
        if path_info is not None:
            target = kwargs.get("target", None)
            if target is not None and target._name == "file":
                path_info = self._path_info()
                return encoder._encode_path(path_info, **kwargs)
        return None

    def _path_info(self):
        if hasattr(self, "_path"):
            from earthkit.data.utils.path_info import LoaderPathInfo

            return LoaderPathInfo(
                self._path,
                binary=self._binary,
                appendable=self._appendable,
                default_encoder=self._default_encoder(),
            )
        return None
