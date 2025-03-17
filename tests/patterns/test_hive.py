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

from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.utils.patterns import HivePattern


@pytest.mark.parametrize("fx", ["hive_fs_1", "hive_fs_2", "hive_fs_3", "hive_fs_4"])
def test_hive_full_scan(request, fx):
    pattern, files = request.getfixturevalue(fx)

    p = HivePattern(pattern, {})
    res_files = p.scan()

    assert sorted(files) == sorted(res_files)


@pytest.mark.parametrize(
    "fx,filters,expected_files",
    [
        (
            "hive_fs_1",
            {"shortName": "z", "step": 6},
            ["/my_root/z_2020-05-11+6.grib", "/my_root/z_2020-05-12+6.grib"],
        ),
        (
            "hive_fs_1",
            {"shortName": ["z", "t"], "step": 6},
            [
                "/my_root/z_2020-05-11+6.grib",
                "/my_root/z_2020-05-12+6.grib",
                "/my_root/t_2020-05-11+6.grib",
                "/my_root/t_2020-05-12+6.grib",
            ],
        ),
        (
            "hive_fs_2",
            {"shortName": "z", "step": 6},
            ["/my_root/z/2020-05-11:6.grib", "/my_root/z/2020-05-12:6.grib"],
        ),
        (
            "hive_fs_2",
            {"shortName": ["z", "t"], "step": 6},
            [
                "/my_root/z/2020-05-11:6.grib",
                "/my_root/z/2020-05-12:6.grib",
                "/my_root/t/2020-05-11:6.grib",
                "/my_root/t/2020-05-12:6.grib",
            ],
        ),
        (
            "hive_fs_3",
            {"shortName": "z", "step": 6},
            ["/my_root/6__/z/my+2020-05-11.grib", "/my_root/6__/z/my+2020-05-12.grib"],
        ),
        (
            "hive_fs_3",
            {"shortName": ["z", "t"], "step": 6},
            [
                "/my_root/6__/z/my+2020-05-11.grib",
                "/my_root/6__/z/my+2020-05-12.grib",
                "/my_root/6__/t/my+2020-05-11.grib",
                "/my_root/6__/t/my+2020-05-12.grib",
            ],
        ),
        (
            "hive_fs_4",
            {"shortName": "z", "step": 6},
            ["/my_root/6__/z/z_2020-05-11.grib", "/my_root/6__/z/z_2020-05-12.grib"],
        ),
        (
            "hive_fs_4",
            {"shortName": ["z", "t"], "step": 6},
            [
                "/my_root/6__/z/z_2020-05-11.grib",
                "/my_root/6__/z/z_2020-05-12.grib",
                "/my_root/6__/t/t_2020-05-11.grib",
                "/my_root/6__/t/t_2020-05-12.grib",
            ],
        ),
    ],
)
def test_hive_filter(request, fx, filters, expected_files):
    pattern, files = request.getfixturevalue(fx)

    # files = _build_fs(md, fs_pattern, date_format)
    print(f"files={files}")

    p = HivePattern(pattern, {})
    res_files = p.scan(filters)

    print(f"res_files={res_files}")

    assert sorted(expected_files) == sorted(res_files)


def test_hive_sel_1():
    from earthkit.data import from_source

    root = earthkit_test_data_file("pattern/1")
    pattern = "{shortName}_{date:date(%Y-%m-%dT%H:%M)}_{step}.grib"

    ds = from_source("hive", os.path.join(root, pattern))

    # assert ds.root == path

    # using hive partitioning keys
    r = ds.sel(shortName="t", step=12)
    assert len(r) == 6

    md_ref = [("t", 1000, 12), ("t", 850, 12), ("t", 700, 12), ("t", 500, 12), ("t", 400, 12), ("t", 300, 12)]
    assert r.metadata("shortName", "level", "step") == md_ref

    # using hive partitioning keys + extra keys from GRIB header
    r = ds.sel(shortName="t", step=12, levtype="pl")
    assert len(r) == 6
