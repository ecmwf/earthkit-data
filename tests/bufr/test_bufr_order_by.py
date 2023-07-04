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
from earthkit.data.testing import earthkit_examples_file


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
        (
            "ident",
            dict(
                ident=[
                    "01001",
                    "01152",
                    "01241",
                    "01400",
                    "01415",
                    "02836",
                    "02963",
                    "03953",
                    "11035",
                    "11747",
                ]
            ),
        ),
    ],
)
def test_bufr_order_by_single_file(
    params,
    expected_meta,
):
    f = from_source("file", earthkit_examples_file("temp_10.bufr"))

    g = f.order_by(params)
    assert len(g) == len(f)

    for k, v in expected_meta.items():
        assert g.metadata(k) == v


@pytest.mark.parametrize(
    "params,expected_meta",
    [
        (
            "ident",
            dict(
                ident=[
                    "01001",
                    "01152",
                    "01400",
                    "01415",
                    "02836",
                    "30823",
                    "30846",
                    "60545",
                    "89514",
                    "91648",
                ]
            ),
        ),
        (
            ["ident"],
            dict(
                ident=[
                    "01001",
                    "01152",
                    "01400",
                    "01415",
                    "02836",
                    "30823",
                    "30846",
                    "60545",
                    "89514",
                    "91648",
                ]
            ),
        ),
        (
            ["dataCategory", "ident"],
            dict(
                dataCategory=[0, 0, 0, 0, 0, 2, 2, 2, 2, 2],
                ident=[
                    "30823",
                    "30846",
                    "60545",
                    "89514",
                    "91648",
                    "01001",
                    "01152",
                    "01400",
                    "01415",
                    "02836",
                ],
            ),
        ),
        (
            dict(ident="ascending"),
            dict(
                ident=[
                    "01001",
                    "01152",
                    "01400",
                    "01415",
                    "02836",
                    "30823",
                    "30846",
                    "60545",
                    "89514",
                    "91648",
                ]
            ),
        ),
        (
            dict(ident="descending"),
            dict(
                ident=[
                    "91648",
                    "89514",
                    "60545",
                    "30846",
                    "30823",
                    "02836",
                    "01415",
                    "01400",
                    "01152",
                    "01001",
                ]
            ),
        ),
    ],
)
def test_bufr_order_by_multi_file(params, expected_meta):
    f1 = from_source("file", earthkit_examples_file("temp_10.bufr"))[:5]
    f2 = from_source("file", earthkit_examples_file("synop_10.bufr"))[:5]
    f = from_source("multi", [f1, f2])

    g = f.order_by(params)
    assert len(g) == len(f)

    for k, v in expected_meta.items():
        assert g.metadata(k) == v


def test_bufr_order_by_with_sel():
    f = from_source("file", earthkit_examples_file("temp_10.bufr"))

    g = f.sel(ident=["01400", "01001", "11035"])
    assert len(g) == 3
    r = g.order_by("ident")
    assert len(r) == len(g)
    assert r.metadata("ident") == ["01001", "01400", "11035"]

    g = f.sel(ident=["01400", "01001", "11035"])
    assert len(g) == 3
    r = g.order_by({"ident": "descending"})
    assert len(r) == len(g)
    assert r.metadata("ident") == ["11035", "01400", "01001"]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
