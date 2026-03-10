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
from earthkit.data.core.temporary import temp_file
from earthkit.data.encoders.grib import GribEncoder
from earthkit.data.targets import to_target
from earthkit.data.utils.testing import NO_RIOXARRAY
from earthkit.data.utils.testing import earthkit_examples_file
from earthkit.data.utils.testing import earthkit_test_data_file


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"encoder": "grib"},
        {"encoder": GribEncoder()},
    ],
)
@pytest.mark.parametrize("direct_call", [True, False])
def test_hl_target_file_grib_core_non_stream(kwargs, direct_call):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.to_fieldlist().values[:, :4]

    with temp_file() as path:
        if direct_call:
            to_target("file", path, data=ds, **kwargs)
        else:
            ds.to_target("file", path, **kwargs)

        ds1 = from_source("file", path).to_fieldlist()
        assert ds1.get("parameter.variable") == ["2t", "msl"]
        assert ds1.get("metadata.shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)


def test_hl_target_file_grib_multi():
    paths = [earthkit_examples_file("test.grib"), earthkit_examples_file("test4.grib")]
    ds = from_source("file", paths)

    with temp_file() as path:
        ds.to_target("file", path)

        ds1 = from_source("file", path)
        assert ds1._TYPE_NAME == "GRIB"
        assert ds1.is_stream() is False
        assert "fieldlist" in ds1.available_types

        fl = ds1.to_fieldlist()
        assert len(fl) == 6
        assert fl.get("parameter.variable") == ["2t", "msl", "t", "z", "t", "z"]
        assert fl[0].shape == (11, 19)
        assert fl[2].shape == (181, 360)


def test_hl_target_file_netcdf_single():
    ds = from_source("file", earthkit_examples_file("test.nc"))

    with temp_file() as path:
        ds.to_target("file", path)

        ds1 = from_source("file", path)
        assert ds1._TYPE_NAME == "NetCDF"
        a = ds.to_xarray()
        assert "t2m" in a.data_vars
        assert "msl" in a.data_vars
        assert a.t2m.shape == (11, 19)
        assert a.msl.shape == (11, 19)


def test_hl_target_file_netcdf_multi():
    paths = [earthkit_test_data_file("era5_2t_1.nc"), earthkit_test_data_file("era5_2t_2.nc")]
    ds = from_source("file", paths)

    with temp_file() as path:
        ds.to_target("file", path)

    # assert ds._TYPE_NAME == "NetCDF"
    # assert ds.is_stream() is False
    # assert "xarray" in ds.available_types
    # assert "fieldlist" in ds.available_types

    # a = ds.to_xarray()
    # assert "t2m" in a.data_vars
    # assert a.t2m.shape == (2, 9, 18)

    # fl = ds.to_fieldlist()
    # assert len(fl) == 2
    # assert fl.get("parameter.variable") == ["t2m", "t2m"]


@pytest.mark.skipif(NO_RIOXARRAY, reason="rioxarray not available")
@pytest.mark.with_proj
def test_hl_target_file_geotiff():
    ds = from_source("file", earthkit_test_data_file("dgm50hs_col_32_368_5616_nw.tif"))
    assert ds._TYPE_NAME == "GeoTIFF"
    # assert len(ds) == 3

    with temp_file() as path:
        ds.to_target("file", path)

        ds1 = from_source("file", path).to_fieldlist()
        assert len(ds1) == 3
        assert ds1[0].get("parameter.variable") == "band_1"


def test_hl_target_file_csv():
    ds = from_source("file", earthkit_test_data_file("test.csv"))

    assert ds._TYPE_NAME == "CSV"
    assert ds.is_stream() is False
    assert "pandas" in ds.available_types

    with temp_file() as path:
        ds.to_target("file", path)

        ds1 = from_source("file", path)
        assert ds1.is_stream() is False
        assert "pandas" in ds1.available_types
        df1 = ds.to_pandas()
        assert len(df1) == 6
        assert list(df1.columns) == ["h1", "h2", "h3", "name"]


def test_hl_target_file_odb():
    ds = from_source("file", earthkit_examples_file("test.odb"))
    assert ds._TYPE_NAME == "ODB"
    assert ds.is_stream() is False
    assert "pandas" in ds.available_types

    with temp_file() as path:
        ds.to_target("file", path)
        ds1 = from_source("file", path)
        assert ds1._TYPE_NAME == "ODB"
        assert ds1.is_stream() is False
        df = ds1.to_pandas()
        assert len(df) == 717
