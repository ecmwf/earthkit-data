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

import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.encoders.grib import GribEncoder
from earthkit.data.targets import to_target
from earthkit.data.testing import earthkit_examples_file


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"encoder": "grib"},
        {"encoder": GribEncoder()},
    ],
)
@pytest.mark.parametrize("direct_call", [True, False])
def test_target_file_pattern_grib_core(kwargs, direct_call):
    ds = from_source("file", earthkit_examples_file("test.grib"))

    with temp_directory() as tmp:
        path = os.path.join(tmp, "{shortName}.grib")

        if direct_call:
            to_target("file-pattern", path, data=ds, **kwargs)
        else:
            ds.to_target("file-pattern", path, **kwargs)

        for name in ("msl", "2t"):
            path = os.path.join(tmp, f"{name}.grib")
            assert os.path.exists(path)
            ds1 = from_source("file", path)
            assert len(ds1) == 1
            assert ds1.metadata("shortName") == [name]


@pytest.mark.parametrize(
    "pattern,expected_value",
    [
        ("{shortName}", {"t": 2, "u": 2, "v": 2}),
        ("{param}", {"t": 2, "u": 2, "v": 2}),
        ("{mars.param}", {"130.128": 2, "131.128": 2, "132.128": 2}),
        ("{shortName}_{level}", {"t_1000": 1, "t_850": 1, "u_1000": 1, "u_850": 1, "v_1000": 1, "v_850": 1}),
        ("{date}_{time}_{step}", {"20180801_1200_0": 6}),
        ("{date}_{time}_{step:03}", {"20180801_1200_000": 6}),
    ],
)
def test_target_file_pattern_grib_keys(pattern, expected_value):
    ds = from_source("file", earthkit_examples_file("test6.grib"))

    with temp_directory() as tmp:
        path = os.path.join(tmp, f"{pattern}.grib")

        to_target(
            "file-pattern",
            path,
            data=ds,
        )

        for k, count in expected_value.items():
            path = os.path.join(tmp, f"{k}.grib")
            assert os.path.exists(path)
            assert len(from_source("file", path)) == count


def test_target_file_pattern_grib_metadata():
    ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    with temp_directory() as tmp:
        # setting GRIB keys for the output
        ds.to_target(
            "file-pattern",
            os.path.join(tmp, "{shortName}_{level}.grib"),
            metadata={"date": 20250108},
            bitsPerValue=8,
        )

        for p in ["t", "u", "v"]:
            path = os.path.join(tmp, f"{p}_850.grib")
            assert os.path.exists(path)
            ds1 = from_source("file", path)
            assert len(ds1) == 1
            assert ds1.metadata("shortName") == [p]
            assert ds1.metadata("level") == [850]
            assert ds1.metadata("date") == [20250108]
            assert ds1.metadata("bitsPerValue") == [8]
