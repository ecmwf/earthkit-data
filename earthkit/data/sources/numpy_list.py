# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.core.fieldlist import Field, FieldList
from earthkit.data.core.index import MaskIndex, MultiIndex

LOG = logging.getLogger(__name__)


class NumpyField(Field):
    def __init__(self, array, metadata):
        self._array = array
        self.__metadata = metadata

    @property
    def _metadata(self):
        return self.__metadata

    @property
    def values(self):
        return self._array


class NumpyFieldList(FieldList):
    def __init__(self, array, metadata, *args, **kwargs):
        self._array = array
        self._metadata = metadata

        if not isinstance(self._metadata, list):
            self._metadata = [self._metadata]

        if self._array.shape[0] != len(self._metadata):
            raise ValueError(
                (
                    f"first array dimension ({self._array.shape[0]}) differs "
                    f"from number of metadata objects ({len(self._metadata)})"
                )
            )

        super().__init__(*args, **kwargs)

    def __getitem__(self, n):
        return NumpyField(self._array[n], self._metadata[n])

    def __len__(self):
        return self._array.shape[0]


class NumpyMaskFieldList(NumpyFieldList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class NumpyMultiFieldList(NumpyFieldList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
