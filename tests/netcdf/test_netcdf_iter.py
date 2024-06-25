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
from earthkit.data.testing import ARRAY_BACKENDS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file


@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("group", ["param"])
def test_netcdf_group_by(array_backend, group):
    ds = from_source("file", earthkit_test_data_file("test6.nc"), array_backend=array_backend)

    ref = [
        [("t", 1000), ("t", 850)],
        [("u", 1000), ("u", 850)],
        [("v", 1000), ("v", 850)],
    ]
    cnt = 0
    for i, f in enumerate(ds.group_by(group)):
        assert len(f) == 2
        assert f.metadata(("param", "level")) == ref[i]
        cnt += len(f)

    assert cnt == len(ds)


@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("group", ["level", ["level", "gridType"]])
def test_netcdf_multi_group_by(array_backend, group):
    ds = from_source(
        "file",
        [earthkit_test_data_file("test4.nc"), earthkit_test_data_file("test6.nc")],
        array_backend=array_backend,
    )

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
def test_netcdf_batched(_kwargs, expected_meta):
    ds = from_source("file", earthkit_test_data_file("test6.nc"))

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
def test_netcdf_multi_batched(_kwargs, expected_meta):
    ds = from_source(
        "file",
        [earthkit_examples_file("test.nc"), earthkit_test_data_file("test4.nc")],
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
