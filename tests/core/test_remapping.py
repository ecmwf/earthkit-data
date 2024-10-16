#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data.core.order import build_remapping
from earthkit.data.utils.xarray.fieldlist import CollectorJoiner

data = {"type": "cf", "number": 0, "name": "t2m"}


def fn(key, **kwargs):
    return data[key]


@pytest.mark.parametrize(
    "remapping,expected_values",
    [
        ({}, {"type": "cf", "number": 0, "name": "t2m"}),
        (None, {"type": "cf", "number": 0, "name": "t2m"}),
        ({"type": "pf"}, {"type": "pf", "number": 0, "name": "t2m"}),
        ({"type": "{type}{number}"}, {"type": "cf0", "name": "t2m"}),
        ({"type": "{type}_{number}"}, {"type": "cf_0", "name": "t2m"}),
        ({"type": lambda: 12}, {"type": 12, "name": "t2m"}),
    ],
)
def test_remapping_dict(remapping, expected_values):
    r = build_remapping(remapping)
    _fn = r(fn)

    for k, v in expected_values.items():
        assert _fn(k) == v


def test_remapping_repeated():
    remapping = {"type": "{type}{number}"}
    r = build_remapping(remapping)
    r = build_remapping(r)
    _fn = r(fn)

    assert _fn("type") == "cf0"


@pytest.mark.parametrize(
    "remapping,patch,expected_values",
    [
        (
            {},
            {"type": {"cf": "pf"}, "number": 12, "name": None},
            {"type": "pf", "number": 12, "name": None},
        ),
        (
            {"type": "{type}{number}"},
            {"type": {"cf0": "x"}},
            {"type": "x", "number": 0, "name": "t2m"},
        ),
        ({}, {"type": lambda x: "x"}, {"type": "x", "number": 0, "name": "t2m"}),
        ({}, {"type": True}, {"type": True, "number": 0, "name": "t2m"}),
        (None, {"type": True}, {"type": True, "number": 0, "name": "t2m"}),
    ],
)
def test_remapping_patch(remapping, patch, expected_values):
    r = build_remapping(remapping, patch)
    _fn = r(fn)

    for k, v in expected_values.items():
        assert _fn(k) == v


def test_remapping_patch_repeated():
    remapping = {"type": "{type}{number}"}
    patch = {"type": {"cf0": "x"}}
    r = build_remapping(remapping, patch)
    r = build_remapping(r)
    _fn = r(fn)

    assert _fn("type") == "x"


@pytest.mark.parametrize(
    "remapping,patch,expected_values",
    [
        (
            {"type": "{type}{number}"},
            None,
            {"type": ("cf0", ("cf", "0")), "number": 0, "name": "t2m"},
        ),
        (
            {"my_type": "{type}{number}"},
            None,
            {"my_type": ("cf0", ("cf", "0")), "type": "cf", "number": 0, "name": "t2m"},
        ),
        (
            {"type": "{type}{number}"},
            {"type": {"cf0": "pf"}, "number": 12, "name": None},
            {"type": ("pf", ("cf", "0")), "number": 12, "name": None},
        ),
        (
            {"my_type": "{type}{number}"},
            {"my_type": {"cf0": "pf"}, "number": 12, "name": None},
            {"my_type": ("pf", ("cf", "0")), "type": "cf", "number": 12, "name": None},
        ),
        (
            {"my_type": "{type}{number}"},
            {"my_type": lambda x: x + "_", "number": 12, "name": None},
            {"my_type": ("cf0_", ("cf", "0")), "type": "cf", "number": 12, "name": None},
        ),
    ],
)
def test_remapping_collector(remapping, patch, expected_values):
    r = build_remapping(remapping, patch)
    _fn = r(fn, joiner=CollectorJoiner)
    for k, v in expected_values.items():
        assert _fn(k) == v


@pytest.mark.parametrize(
    "remapping,patch,expected_values",
    [
        (
            {"type": "{type}{number}"},
            None,
            {"type": ["type", "number"], "number": [], "name": []},
        ),
        (
            {"my_type": "{type}{number}"},
            None,
            {"my_type": ["type", "number"], "type": [], "number": [], "name": []},
        ),
        (
            {"type": "{type}{number}"},
            {"type": {"cf0": "pf"}, "number": 12, "name": None},
            {"type": ["type", "number"], "number": [], "name": []},
        ),
        (
            {"my_type": "{type}{number}"},
            {"my_type": {"cf0": "pf"}, "number": 12, "name": None},
            {"my_type": ["type", "number"], "type": [], "number": [], "name": []},
        ),
    ],
)
def test_remapping_components(remapping, patch, expected_values):
    r = build_remapping(remapping, patch)
    for k, v in expected_values.items():
        assert r.components(k) == v
