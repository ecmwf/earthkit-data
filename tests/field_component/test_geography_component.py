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

from earthkit.data.field.component.geography import SimpleGeography


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            {"latitudes": [-10.0, 0.0, 10.0], "longitudes": [20, 40.0], "shape_hint": (6,)},
            [
                np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
                np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
                (3, 2),
            ],
        ),
        (
            {"latitudes": [-10.0, 0.0, 10.0], "longitudes": [20, 40.0], "shape_hint": (3, 2)},
            [
                np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
                np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
                (3, 2),
            ],
        ),
        (
            {
                "latitudes": np.array([-30.0, -10.0, 0.0, 0.0, 10.0, 50.0]),
                "longitudes": np.array([60.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
                "shape_hint": (6,),
            },
            [
                np.array([-30.0, -10.0, 0.0, 0.0, 10.0, 50.0]),
                np.array([60.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
                (6,),
            ],
        ),
        (
            {
                "latitudes": np.array([-30.0, -10.0, 0.0, 0.0, 10.0, 50.0]),
                "longitudes": np.array([60.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
            },
            [
                np.array([-30.0, -10.0, 0.0, 0.0, 10.0, 50.0]),
                np.array([60.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
                (6,),
            ],
        ),
        (
            {
                "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
                "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
                "shape_hint": (6,),
            },
            [
                np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
                np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
                (6,),
            ],
        ),
        (
            {
                "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
                "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
            },
            [
                np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
                np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
                (6,),
            ],
        ),
        (
            {
                "latitudes": np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
                "longitudes": np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
                "shape_hint": (3, 2),
            },
            [
                np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
                np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
                (3, 2),
            ],
        ),
        (
            {
                "latitudes": np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
                "longitudes": np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
            },
            [
                np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
                np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
                (3, 2),
            ],
        ),
        (
            {
                "latitudes": np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
                "longitudes": np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
                "shape_hint": (6,),  # shape_hint provided but ignored
            },
            [
                np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
                np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
                (3, 2),
            ],
        ),
    ],
)
def test_geography_component_from_dict_ok(input_d, ref):

    if not isinstance(input_d, list):
        input_d = [input_d]

    if isinstance(input_d, list):
        for d in input_d:
            shape_hint = d.pop("shape_hint", None)
            r = SimpleGeography.from_dict(d, shape_hint=shape_hint)

            assert r.shape() == ref[2]
            assert np.allclose(r.latitudes(), ref[0])
            assert np.allclose(r.longitudes(), ref[1])


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            {
                "latitudes": np.array([-20.0, 30.0]),
                "longitudes": np.array([10.0, 50.0]),
            },
            {
                "latitudes": np.array(
                    [-20.0, 30.0],
                ),
                "longitudes": np.array([10.0, 50.0]),
                "shape": (2,),
            },
        ),
    ],
)
def test_geography_component_set(input_d, ref):

    lat_orig = np.array([-10.0, 0.0, 10.0])
    lon_orig = np.array([20.0, 40.0, 60.0])

    r = SimpleGeography.from_dict(
        {
            "latitudes": np.array(lat_orig, copy=True),
            "longitudes": np.array(lon_orig, copy=True),
        }
    )

    if not isinstance(input_d, list):
        input_d = [input_d]

    for d in input_d:
        r1 = r.set(**d)

        for k, v in ref.items():
            if k in ("latitudes", "longitudes"):
                rv = getattr(r1, k)()
                assert np.allclose(rv, v), f"key {k} expected {v} got {rv}"
            else:
                rv = getattr(r1, k)()
                assert rv == v, f"key {k} expected {v} got {rv}"

        # the original object is unchanged
        assert np.allclose(r.latitudes(), lat_orig)
        assert np.allclose(r.longitudes(), lon_orig)
        assert r.shape() == (3,)
