# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.utils.metadata.dict import UserMetadata

from . import Source

LOG = logging.getLogger(__name__)


class FieldlistFromDicts(Source):
    def __init__(self, list_of_dicts, *args, **kwargs):
        self.d = list_of_dicts
        self._kwargs = kwargs

    def mutate(self):
        import numpy as np

        from earthkit.data.indexing.fieldlist import SimpleFieldList

        from .array_list import ArrayField

        fields = []
        for f in self.d:
            v = f["values"]
            if isinstance(v, list):
                v = np.array(v)
            fields.append(ArrayField(v, UserMetadata(f, shape=v.shape)))
        return SimpleFieldList(fields=fields)


source = FieldlistFromDicts
