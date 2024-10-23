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
import yaml

from earthkit.data.testing import earthkit_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from forcings_fixtures import all_params  # noqa: E402
from forcings_fixtures import load_forcings_fs  # noqa: E402


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
def _build_proc_ref(input_data):
    import yaml

    ds, _ = load_forcings_fs(params=all_params, last_step=12, input_data=input_data)
    d = {}
    for p in all_params:
        # print(f"p={p}")
        f = ds.sel(param=p, valid_datetime="2020-05-13T18:00:00")
        v = f[0].values
        d[p] = {
            "first": float(v[0]),
            "last": float(v[-1]),
            "mean": float(np.nanmean(v)),
        }

    # print(d)
    with open("_dev/proc.yaml", "w") as outfile:
        yaml.dump(d, outfile, sort_keys=True)


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
def test_forcings_proc(input_data):
    with open(earthkit_test_data_file(os.path.join("forcings", "proc.yaml")), "r") as f:
        ref = yaml.safe_load(f)

    ds, _ = load_forcings_fs(params=all_params, last_step=12, input_data=input_data)

    for p in all_params:
        f = ds.sel(param=p, valid_datetime="2020-05-13T18:00:00")
        assert len(f) == 1
        v = f[0].values
        r = ref[p]
        assert np.isclose(v[0], r["first"])
        assert np.isclose(v[-1], r["last"])
        assert np.isclose(np.nanmean(v), r["mean"])


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
@pytest.mark.parametrize("param,coord", [("latitude", "lat"), ("longitude", "lon")])
def test_forcings_proc_latlon(input_data, param, coord):
    ds, _ = load_forcings_fs(params=all_params, last_step=12, input_data=input_data)

    latlon = ds[0].to_latlon(flatten=True)
    coord = latlon[coord]
    date = "2020-05-13T18:00:00"

    f = ds.sel(param=param, valid_datetime=date)
    assert len(f) == 1
    assert np.allclose(f[0].values, coord)

    f = ds.sel(param="cos_" + param, valid_datetime=date)
    assert len(f) == 1
    assert np.allclose(f[0].values, np.cos(np.deg2rad(coord)))

    f = ds.sel(param="sin_" + param, valid_datetime=date)
    assert len(f) == 1
    assert np.allclose(f[0].values, np.sin(np.deg2rad(coord)))


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
