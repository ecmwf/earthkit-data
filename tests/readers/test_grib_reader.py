#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_source


def test_grib_len():
    f = from_source("file", "tests/data/test_single.grib")
    assert len(f) == 1

    f = from_source("file", "docs/examples/tuv_pl.grib")
    assert len(f) == 18


def test_grib_create_from_list_of_paths():
    f = from_source("file", ["docs/examples/tuv_pl.grib", "tests/data/ml_data.grib"])

    assert len(f) == 54
    assert f[0].metadata("level") == 1000
    assert f[18].metadata("level") == 1
    assert f[40].metadata("level") == 85


def test_dummy_grib():
    s = from_source(
        "dummy-source",
        kind="grib",
        paramId=[129, 130],
        date=[19900101, 19900102],
        level=[1000, 500],
    )
    assert len(s) == 8


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
