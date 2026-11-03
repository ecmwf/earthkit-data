# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import re
import weakref

from earthkit.data.core import Loader
from earthkit.data.core.caching import cache_file


class Source(Loader):
    """Base class for all sources."""

    name = None
    source_filename = None

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._parent = None

    def _cache_file(self, create, args, **kwargs):
        owner = self.name
        if owner is None:
            owner = re.sub(r"(?!^)([A-Z]+)", r"-\1", self.__class__.__name__).lower()

        return cache_file(owner, create, args, **kwargs)

    @property
    def parent(self):
        """The parent source, if any."""
        if self._parent is None:
            return None
        return self._parent()

    @parent.setter
    def parent(self, parent):
        self._set_parent(weakref.ref(parent))

    def _set_parent(self, parent):
        self._parent = parent

    def _repr_html_(self):
        return self.__repr__()

    def graph(self, depth=0):
        print(" " * depth, self)

    def to_data_object(self):
        """Convert this source into a data object, if possible."""
        from earthkit.data.data.source import DefaultSourceData

        return DefaultSourceData(self)
