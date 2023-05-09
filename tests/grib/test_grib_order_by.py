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

from earthkit.data import from_source
from earthkit.data.testing import earthkit_file


# @pytest.mark.skipif(("GITHUB_WORKFLOW" in os.environ) or True, reason="Not yet ready")
def test_grib_order_by_single_message():
    s = from_source("file", earthkit_file("tests/data/test_single.grib"))

    r = s.order_by("shortName")
    assert len(r) == 1
    assert r[0].metadata("shortName") == "2t"

    r = s.order_by(["shortName"])
    assert len(r) == 1
    assert r[0].metadata("shortName") == "2t"

    r = s.order_by(["shortName", "level"])
    assert len(r) == 1
    assert r[0].metadata("shortName") == "2t"


class _CustomOrder:
    def __call__(self, x, y):
        r = dict(t=2, u=0, v=1)
        a = r[x]
        b = r[y]
        if a == b:
            return 0
        if a > b:
            return 1
        if a < b:
            return -1


@pytest.mark.parametrize(
    "params,expected_meta",
    [
        ("shortName", dict(shortName=["t", "t", "u", "u", "v", "v"])),
        (["shortName"], dict(shortName=["t", "t", "u", "u", "v", "v"])),
        (
            ["shortName", "level"],
            dict(
                shortName=["t", "t", "u", "u", "v", "v"],
                level=[850, 1000, 850, 1000, 850, 1000],
            ),
        ),
        (dict(shortName="ascending"), dict(shortName=["t", "t", "u", "u", "v", "v"])),
        (dict(shortName="descending"), dict(shortName=["v", "v", "u", "u", "t", "t"])),
        (
            dict(shortName="ascending", level="ascending"),
            dict(
                shortName=["t", "t", "u", "u", "v", "v"],
                level=[850, 1000, 850, 1000, 850, 1000],
            ),
        ),
        (
            dict(shortName="ascending", level="descending"),
            dict(
                shortName=["t", "t", "u", "u", "v", "v"],
                level=[1000, 850, 1000, 850, 1000, 850],
            ),
        ),
        (
            dict(shortName=_CustomOrder()),
            dict(shortName=["u", "u", "v", "v", "t", "t"]),
        ),
        (
            dict(shortName=["u", "v", "t"]),
            dict(shortName=["u", "u", "v", "v", "t", "t"]),
        ),
        (
            dict(shortName=["u", "v", "t"], level=[1000, 850]),
            dict(
                shortName=["u", "u", "v", "v", "t", "t"],
                level=[1000, 850, 1000, 850, 1000, 850],
            ),
        ),
    ],
)
def test_grib_order_by_single_file_(
    params,
    expected_meta,
):
    f = from_source("file", earthkit_file("docs/examples/test6.grib"))

    g = f.order_by(params)
    assert len(g) == len(f)

    for k, v in expected_meta.items():
        assert g.metadata(k) == v


@pytest.mark.parametrize(
    "params,expected_meta",
    [
        (
            "shortName",
            dict(shortName=["t", "t", "t", "t", "u", "u", "v", "v", "z", "z"]),
        ),
        (
            ["shortName"],
            dict(shortName=["t", "t", "t", "t", "u", "u", "v", "v", "z", "z"]),
        ),
        (
            ["shortName", "level"],
            dict(
                shortName=["t", "t", "t", "t", "u", "u", "v", "v", "z", "z"],
                level=[500, 850, 850, 1000, 850, 1000, 850, 1000, 500, 850],
            ),
        ),
        (
            dict(shortName="ascending"),
            dict(shortName=["t", "t", "t", "t", "u", "u", "v", "v", "z", "z"]),
        ),
        (
            dict(shortName="descending"),
            dict(shortName=["z", "z", "v", "v", "u", "u", "t", "t", "t", "t"]),
        ),
    ],
)
def test_grib_order_by_multi_file(params, expected_meta):
    f1 = from_source("file", earthkit_file("docs/examples/test4.grib"))
    f2 = from_source("file", earthkit_file("docs/examples/test6.grib"))
    f = from_source("multi", [f1, f2])

    g = f.order_by(params)
    assert len(g) == len(f)

    for k, v in expected_meta.items():
        assert g.metadata(k) == v


def test_grib_order_by_with_sel():
    f = from_source("file", earthkit_file("docs/examples/tuv_pl.grib"))

    g = f.sel(level=500)
    assert len(g) == 3
    r = g.order_by("shortName")
    assert len(r) == len(g)
    assert r.metadata("shortName") == ["t", "u", "v"]

    g = f.sel(level=500)
    assert len(g) == 3
    r = g.order_by({"shortName": "descending"})
    assert len(r) == len(g)
    assert r.metadata("shortName") == ["v", "u", "t"]
