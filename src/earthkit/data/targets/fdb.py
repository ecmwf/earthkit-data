# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import Target

LOG = logging.getLogger(__name__)


class FDBTarget(Target):
    def __init__(self, fdb=None, config=None, **kwargs):
        super().__init__(**kwargs)
        self._fdb = fdb
        self.config = config or {}

    @property
    def fdb(self):
        if self._fdb is None:
            import pyfdb

            self._fdb = pyfdb.FDB(config=self.config)
        return self._fdb

    def flush(self):
        self.fdb.flush()

    def finish(self):
        self.flush()

    def _write_data(self, data, **kwargs):
        d = self.encode(data, **kwargs)
        self.fdb.archive(d.to_bytes())

    def _write_reader(self, reader, **kwargs):
        raise NotImplementedError

    def _write_field(self, field, **kwargs):
        self._write_data(field, **kwargs)

    def _write_fieldlist(self, fieldlist, **kwargs):
        r = self.encode(fieldlist, **kwargs)
        try:
            for d in r:
                self.fdb.archive(d.to_bytes())
        except TypeError:
            self.fdb.archive(r.to_bytes())


target = FDBTarget
