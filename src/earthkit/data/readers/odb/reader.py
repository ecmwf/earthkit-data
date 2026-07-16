# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from .. import Reader

LOG = logging.getLogger(__name__)


class ODBReader(Reader):
    _format = "odb"

    def to_pandas(self, odc_read_odb_kwargs=None):
        try:
            import codc as odc
        except Exception:
            try:
                import pyodc as odc
            except ImportError:
                raise ImportError("ODC handling requires 'pyodc' to be installed")
            LOG.debug("Using pure Python odc decoder.")

        odc_read_odb_kwargs = odc_read_odb_kwargs or {}
        if "single" not in odc_read_odb_kwargs:
            odc_read_odb_kwargs["single"] = True

        return odc.read_odb(self.path, **odc_read_odb_kwargs)

    def to_data_object(self):
        from earthkit.data.data.odb import ODBData

        return ODBData(self)

    def _encode_default(self, encoder, *args, **kwargs):
        return None
