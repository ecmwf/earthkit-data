#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import os
import sys

import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_ARRAYS  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", FL_ARRAYS)
@pytest.mark.parametrize("group", ["param"])
def test_grib_group_by(fl_type, group):
    ds, array_backend = load_grib_data("test6.grib", fl_type)

    ref = [
        [("t", 1000), ("t", 850)],
        [("u", 1000), ("u", 850)],
        [("v", 1000), ("v", 850)],
    ]
    cnt = 0
    for i, f in enumerate(ds.group_by(group)):
        assert len(f) == 2
        assert f.metadata(("param", "level")) == ref[i]
        afl = f.to_fieldlist(array_backend=array_backend.name)
        assert afl is not f
        assert len(afl) == 2
        cnt += len(f)

    assert cnt == len(ds)


@pytest.mark.parametrize("fl_type", FL_ARRAYS)
@pytest.mark.parametrize("group", ["level", ["level", "gridType"]])
def test_grib_multi_group_by(fl_type, group):
    ds, _ = load_grib_data(["test4.grib", "test6.grib"], fl_type)

    ref = [
        [("t", 500), ("z", 500)],
        [("t", 850), ("z", 850), ("t", 850), ("u", 850), ("v", 850)],
        [("t", 1000), ("u", 1000), ("v", 1000)],
    ]
    cnt = 0
    for i, f in enumerate(ds.group_by(group)):
        assert f.metadata(("param", "level")) == ref[i]
        cnt += len(f)

    assert cnt == len(ds)


@pytest.mark.parametrize(
    "_kwargs,expected_meta",
    [
        ({"n": 1}, [["t"], ["u"], ["v"], ["t"], ["u"], ["v"]]),
        ({"n": 3}, [["t", "u", "v"], ["t", "u", "v"]]),
        ({"n": 4}, [["t", "u", "v", "t"], ["u", "v"]]),
    ],
)
def test_grib_batched(_kwargs, expected_meta):
    ds = from_source("file", earthkit_examples_file("test6.grib"))

    cnt = 0
    for i, f in enumerate(ds.batched(_kwargs["n"])):
        assert len(f) == len(expected_meta[i])
        f.metadata("param") == expected_meta[i]
        cnt += len(f)

    assert cnt == len(ds)


@pytest.mark.parametrize(
    "_kwargs,expected_meta",
    [
        ({"n": 1}, [["2t"], ["msl"], ["t"], ["z"], ["t"], ["z"]]),
        ({"n": 2}, [["2t", "msl"], ["t", "z"], ["t", "z"]]),
        ({"n": 3}, [["2t", "msl", "t"], ["z", "t", "z"]]),
        ({"n": 4}, [["2t", "msl", "t", "z"], ["t", "z"]]),
    ],
)
def test_grib_multi_batched(_kwargs, expected_meta):
    ds = from_source(
        "file",
        [earthkit_examples_file("test.grib"), earthkit_examples_file("test4.grib")],
    )

    cnt = 0
    n = _kwargs["n"]
    for i, f in enumerate(ds.batched(n)):
        assert len(f) == len(expected_meta[i])
        f.metadata("param") == expected_meta[i]
        cnt += len(f)

    assert cnt == len(ds)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
