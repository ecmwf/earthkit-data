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


@pytest.mark.parametrize(
    "params,expected_meta,metadata_keys",
    [
        (dict(dataCategory=2), [[2]] * 10, []),
        (dict(dataCategory=2, ident="01400"), [[2, "01400"]], []),
        (
            dict(dataCategory=2, ident=["01400", "11747"]),
            [
                [2, "01400"],
                [2, "11747"],
            ],
            [],
        ),
        (dict(dataCategory=22), [], []),
        (dict(INVALIDKEY="w"), [], []),
        (
            dict(dataCategory=[2], ident=["01400", "11747"], dataSubCategory=101),
            [
                [2, "01400", 101],
                [2, "11747", 101],
            ],
            [],
        ),
    ],
)
def test_bufr_sel_single_file_1(params, expected_meta, metadata_keys):
    f = from_source("file", earthkit_examples_file("temp_10.bufr"))

    g = f.sel(**params)
    assert len(g) == len(expected_meta)
    if len(expected_meta) > 0:
        keys = list(params.keys())
        if metadata_keys:
            keys = metadata_keys

        assert g.metadata(keys) == expected_meta
    return


def test_bufr_sel_single_file_as_dict():
    f = from_source("file", earthkit_examples_file("temp_10.bufr"))
    g = f.sel({"dataCategory": 2, "ident": ["01400", "11747"], "dataSubCategory": 101})
    assert len(g) == 2
    assert g.metadata(["dataCategory", "ident", "dataSubCategory"]) == [
        [2, "01400", 101],
        [2, "11747", 101],
    ]


def test_bufr_sel_multi_file():
    f1 = from_source("file", earthkit_examples_file("temp_10.bufr"))
    f2 = from_source("file", earthkit_examples_file("synop_10.bufr"))
    f = from_source("multi", [f1, f2])

    # single resulting message
    g = f.sel(dataCategory=0, ident="68267")
    assert len(g) == 1
    assert g.metadata(["dataCategory", "ident:s"]) == [[0, "68267"]]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
