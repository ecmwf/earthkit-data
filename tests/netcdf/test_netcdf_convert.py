#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
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
from earthkit.data.testing import earthkit_remote_test_data_file


@pytest.mark.long_test
@pytest.mark.download
def test_netcdf_to_xarray_args():
    # The JD variable in the NetCDF is defined as follows:
    #
    # short JD(time, lat, lon) ;
    #   string JD:long_name = "Date of the first detection" ;
    #   string JD:units = "days since 2022-01-01" ;
    #   string JD:comment = "Possible values: 0  when the pixel is not burned; 1 to 366 day of
    #       the first detection when the pixel is burned; -1 when the pixel is not observed
    #       in the month; -2 when pixel is not burnable: water bodies, bare areas, urban areas,
    #       and permanent snow and ice.
    #
    # when loaded with xarray.open_dataset/xarray.open_mdataset without any kwargs the
    # type of the JD variable is datetime64[ns], which is wrong. The correct type should
    # be int16.

    ds = from_source(
        "url",
        earthkit_remote_test_data_file("test-data", "20220401-C3S-L3S_FIRE-BA-OLCI-AREA_3-fv1.1.nc"),
    )

    r = ds.to_xarray(xarray_open_mfdataset_kwargs=dict(decode_cf=False, decode_times=False))
    assert r["JD"].dtype == "int16"
    r["JD"].shape == (1, 20880, 28440)
    assert np.isclose(r["JD"].values.min(), -2)
    assert np.isclose(r["JD"].values.max(), 120)

    r = ds.to_xarray(decode_cf=False, decode_times=False)
    assert r["JD"].dtype == "int16"
    r["JD"].shape == (1, 20880, 28440)
    assert np.isclose(r["JD"].values.min(), -2)
    assert np.isclose(r["JD"].values.max(), 120)

    r = ds.to_xarray()
    assert r["JD"].dtype == "<M8[ns]"
    r["JD"].shape == (1, 20880, 28440)


if __name__ == "__main__":
    from earthkit.data.testing import main

    # test_datetime()
    main(__file__)
