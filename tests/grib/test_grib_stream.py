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
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file


def repeat_list_items(items, count):
    return sum([[x] * count for x in items], [])


def test_grib_from_stream_invalid_args():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, order_by="level")

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, group_by=1)

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, group_by=["level", 1])

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, group_by="level", batch_size=1)

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(ValueError):
            from_source("stream", stream, batch_size=-1)


@pytest.mark.parametrize("group_by", ["level", ["level", "gridType"]])
def test_grib_from_stream_group_by(group_by):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, group_by=group_by)

        # no methods are available
        with pytest.raises(TypeError):
            len(fs)

        ref = [
            [("t", 1000), ("u", 1000), ("v", 1000)],
            [("t", 850), ("u", 850), ("v", 850)],
        ]
        for i, f in enumerate(fs):
            assert len(f) == 3
            assert f.metadata(("param", "level")) == ref[i]

        # stream consumed, no data is available
        assert sum([1 for _ in fs]) == 0


def test_grib_from_stream_single_batch():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream)

        # no methods are available
        with pytest.raises(TypeError):
            len(fs)

        ref = ["t", "u", "v", "t", "u", "v"]
        val = []
        for f in fs:
            v = f.metadata("param")
            val.append(v)

        assert val == ref

        # stream consumed, no data is available
        assert sum([1 for _ in fs]) == 0


def test_grib_from_stream_multi_batch():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, batch_size=2)

        # no methods are available
        with pytest.raises(TypeError):
            len(fs)

        ref = [["t", "u"], ["v", "t"], ["u", "v"]]
        for i, f in enumerate(fs):
            assert len(f) == 2
            f.metadata("param") == ref[i]

        # stream consumed, no data is available
        assert sum([1 for _ in fs]) == 0


def test_grib_from_stream_in_memory():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, batch_size=0)

        assert len(fs) == 6

        ref = ["t", "u", "v", "t", "u", "v"]
        val = []

        # iteration
        for f in fs:
            v = f.metadata("param")
            val.append(v)

        assert val == ref, "iteration"

        # metadata
        val = []
        val = fs.metadata("param")
        assert val == ref, "method"


def test_grib_save_when_loaded_from_stream():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, batch_size=0)
        assert len(fs) == 6
        with temp_file() as tmp:
            fs.save(tmp)
            fs_saved = from_source("file", tmp)
            assert len(fs) == len(fs_saved)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
