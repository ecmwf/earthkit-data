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

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file

"""
Ideally FieldCube and FieldListTensor should be the same object, however, at the
moment, they are implemented differently.

Main differences:

cube                         tensor
---------------------------------------------
extended_user_shape          full_shape
count()                      -
chninking                    -
Cubelet                      -

When indexing a cube, if the result is a single matching fields the fieldlist returned,
otherwise a cube is returned.

When indexing a tensor always a tensor is returned.
"""


def test_grib_tensor_core():
    ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    c = ds.to_tensor("param", "level")

    assert c.user_shape == (3, 6)
    assert c.field_shape == (7, 12)
    assert c.full_shape == (3, 6, 7, 12)
    assert len(c.source) == 18
    assert c.user_coords == {
        "param": ("t", "u", "v"),
        "level": (300, 400, 500, 700, 850, 1000),
    }

    # this slice is a tensor (in the cube it is a field)
    r = c[0, 0]
    assert r.source[0].shape == (7, 12)
    assert r.source[0].metadata(["param", "level"]) == ["t", 300]
    assert r.source[0].to_numpy().shape == (7, 12)
    assert np.isclose(r.source[0].to_numpy()[0, 0], 226.6531524658203)

    # this slice is a tensor
    r = c[0, 0:2]
    assert r.user_shape == (1, 2)
    assert r.field_shape == (7, 12)
    assert r.full_shape == (1, 2, 7, 12)
    assert r.user_coords == {"param": ("t",), "level": (300, 400)}
    assert len(r.source) == 2
    assert r.to_numpy().shape == (1, 2, 7, 12)
    assert np.isclose(r.to_numpy()[0, 0, 0, 0], 226.6531524658203)

    ref_meta = (["t", 300], ["t", 400])

    for i in range(len(ref_meta)):
        assert r[0, i].source[0].metadata(["param", "level"]) == ref_meta[i], f"{i=} ref_meta={ref_meta[i]}"

    # this slice is a cube
    r = c[1:3, 0:2]
    assert r.user_shape == (2, 2)
    assert r.field_shape == (7, 12)
    assert r.full_shape == (2, 2, 7, 12)
    assert r.user_coords == {"param": ("u", "v"), "level": (300, 400)}
    assert len(r.source) == 4
    assert r.to_numpy().shape == (2, 2, 7, 12)
    assert np.isclose(r.to_numpy()[0, 0, 0, 0], 10.455490112304688)

    ref_meta = (["u", 300], ["u", 400], ["v", 300], ["v", 400])
    cnt = 0
    for par in range(2):
        for level in range(2):
            assert (
                r[par, level].source[0].metadata(["param", "level"]) == ref_meta[cnt]
            ), f"{cnt=} ref_meta={ref_meta[cnt]}"
            cnt += 1

    # this slice is a cube
    r = c[1, ...]
    assert r.user_shape == (1, 6)
    assert r.field_shape == (7, 12)
    assert r.full_shape == (1, 6, 7, 12)
    assert r.user_coords == {"param": ("u",), "level": (300, 400, 500, 700, 850, 1000)}
    assert len(r.source) == 6
    assert r.to_numpy().shape == (1, 6, 7, 12)
    assert np.isclose(r.to_numpy()[0, 0, 0, 0], 10.455490112304688)

    ref_meta = (["u", 300], ["u", 400], ["u", 500], ["u", 700], ["u", 850], ["u", 1000])

    cnt = 0
    for par in range(1):
        for level in range(6):
            assert (
                r[par, level].source[0].metadata(["param", "level"]) == ref_meta[cnt]
            ), f"{cnt=} ref_meta={ref_meta[cnt]}"
            cnt += 1


# def test_grib_cube_non_hypercube():
#     ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
#     ds += from_source("file", earthkit_test_data_file("ml_data.grib"))[:2]
#     assert len(ds) == 18 + 2

#     with pytest.raises(ValueError):
#         ds.cube("param", "level")


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
