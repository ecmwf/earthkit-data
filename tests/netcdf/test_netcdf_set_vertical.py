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

from earthkit.data.utils.testing import earthkit_test_data_file, load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "_kwargs,ref",
    [
        (
            {
                "vertical.level": 320,
                "vertical.level_type": "potential_temperature",
            },
            {
                "vertical.level": 320,
                "vertical.level_type": "potential_temperature",
                "vertical.units": "K",
                "vertical.abbreviation": "pt",
            },
        ),
    ],
)
def test_netcdf_set_vertical(mode, _kwargs, ref):
    ds = load_nc_or_xr_source(earthkit_test_data_file("test4.nc"), mode)

    f = ds[0].set(**_kwargs)

    for k, v in ref.items():
        assert f.get(k) == v

    # the original field is unchanged
    assert ds[0].get("vertical.level") == 500
    assert ds[0].get("vertical.level_type") == "pressure"
