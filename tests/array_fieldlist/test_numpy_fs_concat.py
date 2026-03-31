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
from array_fl_fixtures import (
    check_array_fl,  # noqa: E402
    check_save_to_disk,  # noqa: E402
    load_array_fl,  # noqa: E402
)

from earthkit.data import concat, create_fieldlist, from_source


@pytest.mark.parametrize("mode", ["concat", "multi"])
def test_array_fl_grib_concat_2a(mode):
    ds1, ds2, md = load_array_fl(2)

    if mode == "concat":
        ds = concat(ds1, ds2)
    else:
        ds = from_source("multi", ds1, ds2).to_fieldlist()

    check_array_fl(ds, [ds1, ds2], md)
    check_save_to_disk(ds, 8, md)


def test_array_fl_grib_concat_2b():
    ds1, ds2, md = load_array_fl(2)
    ds1_ori = ds1
    ds1 = concat(ds1, ds2)

    check_array_fl(ds1, [ds1_ori, ds2], md)
    check_save_to_disk(ds1, 8, md)


@pytest.mark.parametrize("mode", ["concat", "multi"])
def test_array_fl_grib_concat_3a(mode):
    ds1, ds2, ds3, md = load_array_fl(3)

    if mode == "concat":
        ds = concat(ds1, ds2)
        ds = concat(ds, ds3)
    else:
        ds = from_source("multi", ds1, ds2).to_fieldlist()
        ds = from_source("multi", ds, ds3).to_fieldlist()

    check_array_fl(ds, [ds1, ds2, ds3], md)
    check_save_to_disk(ds, 26, md)


@pytest.mark.parametrize("mode", ["concat", "multi"])
def test_array_fl_grib_concat_3b(mode):
    ds1, ds2, ds3, md = load_array_fl(3)

    if mode == "concat":
        ds = concat(ds1, ds2, ds3).to_fieldlist()
    else:
        ds = from_source("multi", ds1, ds2, ds3).to_fieldlist()

    check_array_fl(ds, [ds1, ds2, ds3], md)
    check_save_to_disk(ds, 26, md)


def test_array_fl_grib_from_empty_1():
    ds_e = create_fieldlist()
    ds, md = load_array_fl(1)
    ds1 = concat(ds_e, ds)
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    assert ds1.get("parameter.variable") == md
    check_save_to_disk(ds1, 2, md)


def test_array_fl_grib_from_empty_2():
    ds_e = create_fieldlist()
    ds, md = load_array_fl(1)
    ds1 = concat(ds, ds_e)
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    assert ds1.get("parameter.variable") == md
    check_save_to_disk(ds1, 2, md)


def test_array_fl_grib_from_empty_3():
    ds_e = create_fieldlist()
    ds1, ds2, md = load_array_fl(2)
    ds = concat(ds_e, ds1, ds2)

    check_array_fl(ds, [ds1, ds2], md)
    check_save_to_disk(ds, 8, md)


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
