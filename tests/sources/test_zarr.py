#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data import from_source
from earthkit.data.readers.netcdf.field import XArrayField
from earthkit.data.testing import NO_ZARR
from earthkit.data.testing import earthkit_test_data_file


@pytest.mark.skipif(NO_ZARR, reason="Zarr not installed")
def test_zarr_source():
    ds = from_source("zarr", earthkit_test_data_file("test_zarr/"))
    assert len(ds) == 4
    assert isinstance(ds[0], XArrayField)
    assert isinstance(ds[1], XArrayField)
    assert isinstance(ds[2], XArrayField)
    assert isinstance(ds[3], XArrayField)
