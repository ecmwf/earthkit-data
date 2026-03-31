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

import pytest
import yaml

from earthkit.data import FieldList, from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.utils.testing import earthkit_remote_test_data_file, earthkit_test_data_file


def _make_gridspec_list(grid_types):
    d = []
    if isinstance(grid_types, str):
        grid_types = [grid_types]

    for gr in grid_types:
        with open(earthkit_test_data_file(os.path.join("gridspec", f"{gr}.yaml")), "r") as f:
            r = yaml.safe_load(f)
            for t in r:
                assert "file" in t, f"Missing 'file' key in {t}"
                assert "gridspec" in t, f"Missing 'gridspec' key in {t}"
                assert "metadata" in t, f"Missing 'metadata' key in {t}"
            d.extend(r)

    # print(d)
    return d


def gridspec_list(grid_types):
    if isinstance(grid_types, str):
        grid_types = [grid_types]

    for item in _make_gridspec_list(grid_types):
        yield (item["metadata"], item["gridspec"], item["file"])


def test_grib_gridspec_from_file():
    ds = from_source(
        "file",
        earthkit_test_data_file(os.path.join("gridspec", "t_75_-60_10_40_5x5.grib1")),
    ).to_fieldlist()

    ref = {
        # "type": "regular_ll",
        "grid": [5.0, 5.0],
        "area": [75.0, -60.0, 10.0, 40.0],
        # "j_points_consecutive": 0,
        # "i_scans_negatively": 0,
        # "j_scans_positively": 0,
    }
    gs = ds[0].geography.grid_spec()
    assert isinstance(gs, dict), type(gs)
    assert gs == ref


@pytest.mark.parametrize(
    "input_file",
    [
        # "grids/reduced_gg/O32_global.grib1",
        "grids/reduced_gg/O32_global.grib2",
        # "grids/healpix/H4_ring.grib2",
        # "grids/healpix/H4_nested.grib2",
    ],
)
def test_grib_gridspec_to_fieldlist(input_file):
    import numpy as np

    def make_lat_lon(dx):
        lat_v = np.linspace(90, -90, int(180 / dx) + 1)
        lon_v = np.linspace(0, 360 - dx, int(360 / dx))
        lon, lat = np.meshgrid(lon_v, lat_v)
        return lat, lon

    ds_in = from_source(
        "url",
        earthkit_remote_test_data_file(input_file),
    ).to_fieldlist()

    # target grid: 5x5
    gs = {"grid": [5, 5]}
    v = np.random.rand(37, 72)

    ds = FieldList.from_fields([x.set({"values": v.flatten(), "geography.grid_spec": gs}) for x in ds_in])

    # md = ds_in[0].metadata().override(gridspec=gs)
    # ds = FieldList.from_numpy(v.flatten(), md)

    assert len(ds) == 1

    # make references
    ref_base = dict(
        Ni=72,
        Nj=37,
        Nx=72,
        Ny=37,
        gridType="regular_ll",
        iDirectionIncrementInDegrees=5.0,
        iScansNegatively=0,
        jDirectionIncrementInDegrees=5.0,
        jPointsAreConsecutive=0,
        jScansPositively=0,
        latitudeOfFirstGridPointInDegrees=90.0,
        latitudeOfLastGridPointInDegrees=-90.0,
        longitudeOfFirstGridPointInDegrees=0.0,
        longitudeOfLastGridPointInDegrees=355.0,
    )

    ref = {"metadata." + k: v for k, v in ref_base.items()}

    lat_ref, lon_ref = make_lat_lon(5)

    # check latlon
    lat, lon = ds[0].geography.latlons()
    assert np.allclose(lat.flatten(), lat_ref.flatten())
    assert np.allclose(lon.flatten(), lon_ref.flatten())
    assert ds[0].shape == (37, 72)
    assert np.allclose(ds[0].to_numpy().shape, (37, 72))

    # check metadata
    # res = {k: ds[0].get(k) for k in ref.keys()}
    # res = {k: ds[0].get(k) for k in ref.keys()}
    # assert res == ref

    # save
    with temp_file() as tmp:
        ds.to_target("file", tmp)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp).to_fieldlist()

        # values
        v_tmp = r_tmp[0].values
        assert np.allclose(v_tmp, v.flatten(), atol=1e-3)

        # latlon
        lat, lon = r_tmp[0].geography.latlons()
        assert np.allclose(lat.flatten(), lat_ref.flatten())
        assert np.allclose(lon.flatten(), lon_ref.flatten())

        v_tmp = r_tmp[0].values
        assert np.allclose(v_tmp, v.flatten(), atol=1e-3)
        res = {k: r_tmp[0].get(k) for k in ref.keys()}
        assert res == ref


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main()
