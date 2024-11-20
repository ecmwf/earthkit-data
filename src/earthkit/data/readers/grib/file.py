# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.readers import Reader
from earthkit.data.readers.grib.index.file import GribFieldListInOneFile

LOG = logging.getLogger(__name__)


class GRIBReader(GribFieldListInOneFile, Reader):
    appendable = True  # GRIB messages can be added to the same file

    def __init__(self, source, path, parts=None):
        _kwargs = {}
        for k in [
            # "array_backend",
            "grib_field_policy",
            "grib_handle_policy",
            "grib_handle_cache_size",
            "use_grib_metadata_cache",
        ]:
            _kwargs[k] = source._kwargs.get(k, None)

        for k in source._kwargs:
            if "-" in k:
                raise KeyError(f"Invalid option {k} in GRIBReader. Option names must not contain '-'.")

        Reader.__init__(self, source, path)
        GribFieldListInOneFile.__init__(self, path, parts=parts, **_kwargs)

    def __repr__(self):
        return "GRIBReader(%s)" % (self.path,)

    def mutate_source(self):
        # A GRIBReader is a source itself
        return self

    def is_streamable_file(self):
        return True

    def __getstate__(self):
        r = {"kwargs": self.source._kwargs, "messages": []}
        for f in self:
            r["messages"].append(f.message())
        return r

    def __setstate__(self, state):
        from earthkit.data import from_source
        from earthkit.data.core.caching import cache_file

        def _create(path, args):
            with open(path, "wb") as f:
                for message in state["messages"]:
                    f.write(message)

        path = cache_file(
            "GRIBReader",
            _create,
            [],
        )
        ds = from_source("file", path)
        self.__init__(ds.source, path)
