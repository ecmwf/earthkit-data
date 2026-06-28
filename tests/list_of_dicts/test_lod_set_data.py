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
from lod_fixtures import build_lod_fieldlist  # noqa: E402

from earthkit.data import FieldList


@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_set_data_field(lod_ll_flat, mode):
    ds_ori = build_lod_fieldlist(lod_ll_flat, mode)

    vals_ori = ds_ori[0].values

    f = ds_ori[0].set(values=vals_ori + 1)

    assert f.get("parameter.variable") == "t"
    assert f.get("vertical.level") == 500
    assert np.allclose(f.values, vals_ori + 1)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].set(values=vals_ori + 1)
    f = f.set(values=vals_ori + 2)

    assert f.get("parameter.variable") == "t"
    assert f.get("vertical.level") == 500
    assert np.allclose(f.values, vals_ori + 2)
    assert np.allclose(ds_ori[0].values, vals_ori)


@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_set_data_fieldlist(lod_ll_flat, mode):
    ds_ori = build_lod_fieldlist(lod_ll_flat, mode)

    vals_ori = ds_ori[0].values

    fields = []
    for i in range(2):
        f = ds_ori[i].set(values=vals_ori + i + 1)
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.get("parameter.variable") == ["t", "t"]
    assert ds.get("vertical.level") == [500, 850]
    assert np.allclose(ds[0].values, vals_ori + 1)
    assert np.allclose(ds[1].values, vals_ori + 2)
