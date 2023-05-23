#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

from earthkit.data.readers.netcdf import cf

NO_CARTOPY = False
try:
    import cartopy.crs as ccrs
except ImportError:
    NO_CARTOPY = True


def test_CFParameters():
    params = {
        "latitude_of_projection_origin": 52,
        "longitude_of_projection_origin": 10,
        "standard_parallel": 40,
    }

    cf_parameters = cf.CFParameters(**params)

    assert cf_parameters.central_latitude == 52
    assert cf_parameters.central_longitude == 10
    assert cf_parameters.standard_parallels == [40]


@pytest.mark.skipif(NO_CARTOPY, reason="cartopy is not installed")
def test_CFGridMapping():
    grid_mapping = {
        "grid_mapping_name": "lambert_azimuthal_equal_area",
        "latitude_of_projection_origin": 52.0,
        "longitude_of_projection_origin": 10.0,
        "false_northing": 3210000.0,
        "false_easting": 4321000.0,
    }
    grid_mapping = cf.CFGridMapping.from_grid_mapping(**grid_mapping)

    assert grid_mapping.to_ccrs() == ccrs.LambertAzimuthalEqualArea(
        central_longitude=10.0,
        central_latitude=52.0,
        false_easting=4321000.0,
        false_northing=3210000.0,
    )
