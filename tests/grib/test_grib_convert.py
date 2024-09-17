#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import sys

import numpy as np
import pytest

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ["numpy"])
def test_icon_to_xarray(fl_type, array_backend):
    # test the conversion to xarray for an icon (unstructured grid) grib file.
    g = load_grib_data("test_icon.grib", fl_type, array_backend, folder="data")

    ds = g.to_xarray()
    assert len(ds.data_vars) == 1
    # Dataset contains 9 levels and 9 grid points per level
    ref_levs = g.metadata("level")
    assert ds["pres"].sizes["generalVerticalLayer"] == len(ref_levs)
    assert ds["pres"].sizes["values"] == 6


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ["numpy"])
def test_to_xarray_filter_by_keys(fl_type, array_backend):
    g = load_grib_data("tuv_pl.grib", fl_type, array_backend)
    g = g.sel(param="t", level=500) + g.sel(param="u")
    assert len(g) > 1

    # see github #250
    r = g.to_xarray(xarray_open_dataset_kwargs={"backend_kwargs": {"filter_by_keys": {"shortName": "t"}}})

    assert len(r.data_vars) == 1
    assert r["t"].sizes["isobaricInhPa"] == 1


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ["numpy"])
def test_grib_to_pandas(fl_type, array_backend):
    f = load_grib_data("test_single.grib", fl_type, array_backend, folder="data")

    # all points
    df = f.to_pandas()
    assert len(df) == 84
    cols = [
        "lat",
        "lon",
        "value",
        "datetime",
        "domain",
        "levtype",
        "date",
        "time",
        "step",
        "param",
        "class",
        "type",
        "stream",
        "expver",
    ]
    assert list(df.columns) == cols
    assert np.allclose(df["lat"][0:2], [90, 90])
    assert np.allclose(df["lon"][0:2], [0, 30])
    assert np.allclose(df["value"][0:2], [260.435608, 260.435608])

    # specific location
    df = f.to_pandas(latitude=90, longitude=30)
    assert len(df) == 1
    assert list(df.columns) == cols
    assert np.isclose(df["lat"][0], 90)
    assert np.isclose(df["lon"][0], 30)
    assert np.isclose(df["value"][0], 260.435608)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
