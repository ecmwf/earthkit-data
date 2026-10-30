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

import earthkit.data as ekd


@pytest.mark.parametrize("dtype", [int, float, np.int32, np.int64, np.float32, np.float64, "mixed"])
def test_xr_engine_numpy_int_levels_single(dtype):
    parameter = {"variable": "t", "units": "K"}

    fl = []
    for level in range(1, 22):
        if dtype == "mixed":
            if level in [9, 10, 11, 12]:
                level_val = np.int64(level)
            else:
                level_val = level
        else:
            level_val = dtype(level)

        vertical = {"level": level_val, "level_type": "hybrid"}
        values = np.array([level, level], dtype=np.float64)

        fl.append(ekd.Field.from_components(values=values, parameter=parameter, vertical=vertical))

    fl = ekd.FieldList.from_fields(fl)
    assert len(fl) == 21

    ds = fl.to_xarray()

    assert ds.dims["level"] == 21
    assert ds["level"].values.tolist() == list(range(1, 22))


def test_xr_engine_numpy_int_levels_concat():
    dtype = np.int64

    fl1 = []
    for level in range(1, 22):
        level_val = dtype(level)
        vertical = {"level": level_val, "level_type": "hybrid"}
        values = np.array([level, level], dtype=np.float64)
        parameter = {"variable": "t", "units": "K"}
        f = ekd.Field.from_components(values=values, parameter=parameter, vertical=vertical)
        fl1.append(f)

    fl2 = []
    for level in range(1, 22):
        vertical = {"level": level, "level_type": "hybrid"}
        values = np.array([level, level], dtype=np.float64)
        parameter = {"variable": "q", "units": "kg/kg"}
        f = ekd.Field.from_components(values=values, parameter=parameter, vertical=vertical)
        fl2.append(f)

    fl1 = ekd.FieldList.from_fields(fl1)
    assert len(fl1) == 21

    fl2 = ekd.FieldList.from_fields(fl2)
    assert len(fl2) == 21

    fl3 = ekd.concat(fl1, fl2)

    ds = fl3.to_xarray()

    assert ds.dims["level"] == 21
    assert ds["level"].values.tolist() == list(range(1, 22))
