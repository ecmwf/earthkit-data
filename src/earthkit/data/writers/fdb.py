# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.encoders import _find_encoder

from . import Target

LOG = logging.getLogger(__name__)


class FDBTarget(Target):
    def __init__(self, fdb):
        self._fdb = fdb

    @property
    def fdb(self):
        if self._fdb is None:
            import pyfdb

            self._fdb = pyfdb.FDB()
        return self._fdb

    def write(self, data, data_format=None, encoder=None, **kwargs):
        encoder = _find_encoder(data, encoder, data_format, **kwargs)

        d = encoder.encode(data, **kwargs)
        self.fdb.archive(d.message())

    # fdb.flush()
