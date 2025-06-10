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

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.targets import to_target
from earthkit.data.testing import NO_ZARR


@pytest.mark.skipif(NO_ZARR, reason="Zarr not installed")
@pytest.mark.cache
@pytest.mark.parametrize("direct_call", [True, False])
def test_target_zarr_from_grib(direct_call):
    ds = from_source("sample", "pl.grib")

    with temp_directory() as tmp:
        path = os.path.join(tmp, "_res.zarr")

        if direct_call:
            to_target(
                "zarr",
                earthkit_to_xarray_kwargs={"chunks": {"forecast_reference_time": 1, "step": 1, "level": 1}},
                xarray_to_zarr_kwargs={"store": path, "mode": "w"},
                data=ds,
            )
        else:
            ds.to_target(
                "zarr",
                earthkit_to_xarray_kwargs={"chunks": {"forecast_reference_time": 1, "step": 1, "level": 1}},
                xarray_to_zarr_kwargs={"store": path, "mode": "w"},
            )

        import zarr

        root = zarr.group(path)
        assert root

        shapes = {
            "t": (4, 2, 2, 19, 36),
            "r": (4, 2, 2, 19, 36),
            "forecast_reference_time": (4,),
            "step": (2,),
            "level": (2,),
            "latitude": (19,),
            "longitude": (36,),
        }

        for k in ["t", "r", "forecast_reference_time", "step", "level", "latitude", "longitude"]:
            k in root, f"Key {k} not found in Zarr root"
            assert (
                root[k].shape == shapes[k]
            ), f"Shape mismatch for {k}: expected {shapes[k]}, got {root[k].shape}"
