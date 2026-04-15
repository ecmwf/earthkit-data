# (C) Copyright 2020- ECMWF.  #
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import ABCMeta, abstractmethod


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
        """Double dispatch to the encoder."""
        pass


class Loader(Base):
    """Base class for all objects that can be loaded using a loader."""

    @abstractmethod
    def _cache_file(self, *args, **kwargs):
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
