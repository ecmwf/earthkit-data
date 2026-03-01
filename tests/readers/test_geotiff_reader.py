#!/usr/bin/env python3

# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.field import Field
from earthkit.data.utils.projections import TransverseMercator
from earthkit.data.utils.testing import NO_RIOXARRAY
from earthkit.data.utils.testing import earthkit_test_data_file


@pytest.mark.skipif(NO_RIOXARRAY, reason="rioxarray not available")
@pytest.mark.with_proj
@pytest.mark.parametrize(
    "fname", [("dgm50hs_col_32_368_5616_nw.tif"), ("dgm50hs_col_32_368_5616_nw_bigtiff.tiff")]
)
def test_geotiff_reader_with_multiband(fname):
    s = from_source("file", earthkit_test_data_file(fname))
    assert len(s) == 3
    assert isinstance(s[0], Field)
    assert isinstance(s[1], Field)
    assert s[0].get("parameter.variable") == "band_1"
    assert s[1].get("parameter.variable") == "band_2"
    assert s[2].get("parameter.variable") == "band_3"
    # assert s[0].get("band") == 1
    # assert s[1].get("band") == 2
    # assert s[2].get("band") == 3
    assert isinstance(s.geography.projection(), TransverseMercator)
    assert s[0].shape == (294, 315)
    assert np.allclose(s[0].geography.latitudes()[0, 0:2], np.array([7.12620136, 7.12692213]))
    assert np.allclose(s[0].geography.longitudes()[0, 0:2], np.array([50.82441594, 50.82442752]))


@pytest.mark.skipif(NO_RIOXARRAY, reason="rioxarray not available")
@pytest.mark.with_proj
def test_geotiff_bypassing_xr_engine():
    import xarray as xr

    # the earthkit xarray engine should not try to handle this file but leave it to the rioxarray backend
    da = xr.open_dataarray(earthkit_test_data_file("dgm50hs_col_32_368_5616_nw.tif"))
    assert da.name == "band_data"


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
