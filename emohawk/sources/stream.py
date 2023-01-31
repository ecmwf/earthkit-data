# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from emohawk.readers.grib.memory import FieldSetInMemory

from . import Source

LOG = logging.getLogger(__name__)


class GribStream(Source):
    def __init__(self, stream):
        self._reader = FieldSetInMemory(self, stream)

    def __iter__(self):
        return iter(self._reader)

    def __len__(self):
        return len(self._reader)

    def __getitem__(self, n):
        return self._reader[n]

    def sel(self, *args, **kwargs):
        return self._reader.sel(*args, **kwargs)

    def order_by(self, *args, **kwargs):
        return self._reader.order_by(*args, **kwargs)

    def to_xarray(self, **kwargs):
        return self._reader.to_xarray(**kwargs)

    def to_pandas(self, **kwargs):
        LOG.debug("Calling reader.to_pandas %s", self)
        return self._reader.to_pandas(**kwargs)

    def to_numpy(self, **kwargs):
        return self._reader.to_numpy(**kwargs)

    @property
    def values(self):
        return self._reader.values

    def save(self, path):
        return self._reader.save(path)

    def write(self, f):
        return self._reader.write(f)

    def scaled(self, *args, **kwargs):
        return self._reader.scaled(*args, **kwargs)

    def _attributes(self, names):
        return self._reader._attributes(names)

    # def __fspath__(self):
    #     return self.path

    def metadata(self, *args, **kwargs):
        return self._reader.metadata(*args, **kwargs)

    def ls(self, *args, **kwargs):
        return self._reader.ls(*args, **kwargs)

    def describe(self, *args, **kwargs):
        return self._reader.describe(*args, **kwargs)

    # Used by normalisers
    def to_datetime(self):
        return self._reader.to_datetime()

    def to_datetime_list(self):
        return self._reader.to_datetime_list()

    def to_bounding_box(self):
        return self._reader.to_bounding_box()

    def statistics(self, **kwargs):
        return self._reader.statistics(**kwargs)


source = GribStream
