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
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file


def test_grib_cube():
    ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    c = ds.cube("param", "level")

    assert c.user_shape == (3, 6)
    assert c.field_shape == (7, 12)
    assert c.extended_user_shape == (3, 6, 7, 12)
    assert c.count() == 18

    # this slice is a field
    r = c[0, 0]
    assert r.shape == (7, 12)
    assert r.metadata(["param", "level"]) == ["t", 300]
    assert r.to_numpy().shape == (7, 12)
    assert np.isclose(r.to_numpy()[0, 0], 226.6531524658203)

    # this slice is a cube
    r = c[0, 0:2]
    assert r.user_shape == (1, 2)
    assert r.field_shape == (7, 12)
    assert r.extended_user_shape == (1, 2, 7, 12)
    assert r.count() == 2
    assert r.to_numpy().shape == (1, 2, 7, 12)
    assert np.isclose(r.to_numpy()[0, 0, 0, 0], 226.6531524658203)

    ref_meta = (["t", 300], ["t", 400])

    for i in range(len(ref_meta)):
        assert r[0, i].metadata(["param", "level"]) == ref_meta[i], f"{i=} ref_meta={ref_meta[i]}"

    # this slice is a cube
    r = c[1:3, 0:2]
    assert r.user_shape == (2, 2)
    assert r.field_shape == (7, 12)
    assert r.extended_user_shape == (2, 2, 7, 12)
    assert r.count() == 4
    assert r.to_numpy().shape == (2, 2, 7, 12)
    assert np.isclose(r.to_numpy()[0, 0, 0, 0], 10.455490112304688)

    ref_meta = (["u", 300], ["u", 400], ["v", 300], ["v", 400])
    cnt = 0
    for par in range(2):
        for level in range(2):
            assert (
                r[par, level].metadata(["param", "level"]) == ref_meta[cnt]
            ), f"{cnt=} ref_meta={ref_meta[cnt]}"
            cnt += 1

    # this slice is a cube
    r = c[1, ...]
    assert r.user_shape == (1, 6)
    assert r.field_shape == (7, 12)
    assert r.extended_user_shape == (1, 6, 7, 12)
    assert r.count() == 6
    assert r.to_numpy().shape == (1, 6, 7, 12)
    assert np.isclose(r.to_numpy()[0, 0, 0, 0], 10.455490112304688)

    ref_meta = (["u", 300], ["u", 400], ["u", 500], ["u", 700], ["u", 850], ["u", 1000])

    cnt = 0
    for par in range(1):
        for level in range(6):
            assert (
                r[par, level].metadata(["param", "level"]) == ref_meta[cnt]
            ), f"{cnt=} ref_meta={ref_meta[cnt]}"
            cnt += 1


def test_grib_cubelet():
    ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    c = ds.cube("param", "level")

    reading_chunks = None
    assert c.count(reading_chunks) == 18

    ic = []
    for i in range(3):
        for j in range(6):
            ic.append((i, j))

    ref = [
        226.6531524658203,
        244.00323486328125,
        255.8430633544922,
        271.26531982421875,
        272.53916931152344,
        272.5641784667969,
        10.455490112304688,
        6.213775634765625,
        4.7400054931640625,
        4.1455230712890625,
        -4.89837646484375,
        -6.2868804931640625,
        -3.07965087890625,
        -0.050384521484375,
        -0.9900970458984375,
        3.6385498046875,
        8.660964965820312,
        7.8334808349609375,
    ]

    for i, cb in enumerate(c.iterate_cubelets(reading_chunks)):
        assert cb.extended_icoords == ic[i]

    for i, cb in enumerate(c.iterate_cubelets(reading_chunks)):
        assert cb.to_numpy().shape == (7, 12)
        assert np.isclose(cb.to_numpy()[0, 0], ref[i])


def test_grib_cube_non_hypercube():
    ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    ds += from_source("file", earthkit_test_data_file("ml_data.grib"))[:2]
    assert len(ds) == 18 + 2

    with pytest.raises(ValueError):
        ds.cube("param", "level")


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
