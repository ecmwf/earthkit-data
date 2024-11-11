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
    def __init__(self, fdb, config=None, **kwargs):
        super().__init__(**kwargs)
        self._fdb = fdb
        self.config = config or {}

    @property
    def fdb(self):
        if self._fdb is None:
            import pyfdb

            self._fdb = pyfdb.FDB(config=self.config)
        return self._fdb

    def write(self, data=None, encoder=None, template=None, **kwargs):
        from earthkit.data.core.fieldlist import FieldList

        if encoder is None:
            encoder = self._coder

        if template is None:
            template = self.template

        if isinstance(data, FieldList):
            data.to_target(self, encoder=encoder, template=template, **kwargs)
        else:
            encoder = _find_encoder(data, encoder, template=template, **kwargs)

            d = encoder.encode(data)
            self.fdb.archive(d.get_message())

    def flush(self):
        self.fdb.flush()
