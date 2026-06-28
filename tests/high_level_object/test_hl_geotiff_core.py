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
from earthkit.data.utils.testing import NO_RIOXARRAY, earthkit_test_data_file


@pytest.mark.skipif(NO_RIOXARRAY, reason="rioxarray not available")
def test_hl_geotiff_single_core():
    ds = from_source("file", earthkit_test_data_file("dgm50hs_col_32_368_5616_nw.tif"))

    assert ds._TYPE_NAME == "GeoTIFF"
    assert ds.is_stream() is False
    assert "xarray" in ds.available_types
    assert "fieldlist" in ds.available_types

    a = ds.to_xarray()
    assert "band_1" in a.data_vars
    assert "band_2" in a.data_vars
    assert "band_3" in a.data_vars
    assert a.band_1.shape == (294, 315)
    assert a.band_2.shape == (294, 315)
    assert a.band_3.shape == (294, 315)

    fl = ds.to_fieldlist()
    assert len(fl) == 3
    assert fl.get("parameter.variable") == ["band_1", "band_2", "band_3"]
