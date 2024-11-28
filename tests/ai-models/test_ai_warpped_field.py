#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

import numpy as np

from earthkit.data import SimpleFieldList
from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file

LOG = logging.getLogger(__name__)


class WrappedField:
    def __init__(self, field):
        self._field = field

    def __getattr__(self, name):
        return getattr(self._field, name)

    def __repr__(self) -> str:
        return repr(self._field)


class NewDataField(WrappedField):
    def __init__(self, field, data):
        super().__init__(field)
        self._data = data
        self.shape = data.shape

    def to_numpy(self, flatten=False, dtype=None, index=None):
        data = self._data
        if dtype is not None:
            data = data.astype(dtype)
        if flatten:
            data = data.flatten()
        if index is not None:
            data = data[index]
        return data


class NewMetadataField(WrappedField):
    def __init__(self, field, **kwargs):
        super().__init__(field)
        self._metadata = kwargs

    def metadata(self, *args, **kwargs):
        if len(args) == 1 and args[0] in self._metadata:
            return self._metadata[args[0]]
        return self._field.metadata(*args, **kwargs)


def test_ai_models_wrapped_field_grib():

    ds = from_source("file", earthkit_examples_file("test.grib"))
    np_ref = ds.to_numpy()
    vals_ref = ds.values

    f1 = NewMetadataField(ds[0], shortName="sstk")
    f2 = NewMetadataField(ds[1], shortName="2d")

    r = SimpleFieldList([f1, f2])

    assert r[0].metadata("shortName") == "sstk"
    assert r[1].metadata("shortName") == "2d"
    assert np.allclose(r.to_numpy(), np_ref)
    assert np.allclose(r.values, vals_ref)
