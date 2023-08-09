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
from earthkit.data.testing import earthkit_examples_file, earthkit_test_data_file
from earthkit.data.utils import projections


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


@pytest.mark.parametrize("index", [0, None])
def test_grib_to_latlon_single(index):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    eps = 1e-5
    g = f[index] if index is not None else f
    v = g.to_latlon(flatten=True)
    assert isinstance(v, dict)
    assert isinstance(v["lon"], np.ndarray)
    assert isinstance(v["lat"], np.ndarray)
    check_array(
        v["lon"],
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        v["lat"],
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


@pytest.mark.parametrize("index", [0, None])
def test_grib_to_latlon_single_shape(index):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    g = f[index] if index is not None else f
    v = g.to_latlon()
    assert isinstance(v, dict)
    assert isinstance(v["lon"], np.ndarray)
    assert isinstance(v["lat"], np.ndarray)

    # x
    assert v["lon"].shape == (7, 12)
    for x in v["lon"]:
        assert np.allclose(x, np.linspace(0, 330, 12))

    # y
    assert v["lat"].shape == (7, 12)
    for i, y in enumerate(v["lat"]):
        assert np.allclose(y, np.ones(12) * (90 - i * 30))


def test_grib_to_latlon_multi():
    f = from_source("file", earthkit_examples_file("test.grib"))

    v_ref = f[0].to_latlon(flatten=True)
    v = f.to_latlon(flatten=True)
    assert isinstance(v, dict)
    assert v.keys() == v_ref.keys()

    assert isinstance(v, dict)
    assert np.allclose(v["lat"], v_ref["lat"])
    assert np.allclose(v["lon"], v_ref["lon"])


def test_grib_to_latlon_multi_non_shared_grid():
    f1 = from_source("file", earthkit_examples_file("test.grib"))
    f2 = from_source("file", earthkit_examples_file("test4.grib"))
    f = f1 + f2

    with pytest.raises(ValueError):
        f.to_latlon()


@pytest.mark.parametrize("index", [0, None])
def test_grib_to_points_single(index):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    eps = 1e-5
    g = f[index] if index is not None else f
    v = g.to_points(flatten=True)
    assert isinstance(v, dict)
    assert isinstance(v["x"], np.ndarray)
    assert isinstance(v["y"], np.ndarray)
    check_array(
        v["x"],
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        v["y"],
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


def test_grib_to_points_unsupported_grid():
    f = from_source("file", earthkit_test_data_file("mercator.grib"))
    with pytest.raises(ValueError):
        f[0].to_points()


def test_grib_to_points_multi():
    f = from_source("file", earthkit_examples_file("test.grib"))

    v_ref = f[0].to_points(flatten=True)
    v = f.to_points(flatten=True)
    assert isinstance(v, dict)
    assert v.keys() == v_ref.keys()

    assert isinstance(v, dict)
    assert np.allclose(v["x"], v_ref["x"])
    assert np.allclose(v["y"], v_ref["y"])


def test_grib_to_points_multi_non_shared_grid():
    f1 = from_source("file", earthkit_examples_file("test.grib"))
    f2 = from_source("file", earthkit_examples_file("test4.grib"))
    f = f1 + f2

    with pytest.raises(ValueError):
        f.to_points()


def test_bbox():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    bb = ds.bounding_box()
    assert len(bb) == 2
    for b in bb:
        assert b.as_tuple() == (73, -27, 33, 45)


@pytest.mark.parametrize("index", [0, None])
def test_grib_projection_ll(index):
    f = from_source("file", earthkit_examples_file("test.grib"))

    if index is not None:
        g = f[index]
    else:
        g = f
    assert isinstance(
        g.projection(), (projections.EquidistantCylindrical, projections.LongLat)
    )


def test_grib_projection_mercator():
    f = from_source("file", earthkit_test_data_file("mercator.grib"))
    projection = f[0].projection()
    assert isinstance(projection, projections.Mercator)
    assert projection.parameters == {
        "true_scale_latitude": 20,
        "central_latitude": 0,
        "central_longitude": 0,
        "false_easting": 0,
        "false_northing": 0,
    }
    assert projection.globe == dict()


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
