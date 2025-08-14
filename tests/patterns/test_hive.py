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
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.utils.patterns import HivePattern


@pytest.mark.parametrize("fx", ["hive_fs_1", "hive_fs_2", "hive_fs_3", "hive_fs_4", "hive_fs_5"])
def test_hive_full_scan(request, fx):
    pattern, files, _ = request.getfixturevalue(fx)

    p = HivePattern(pattern, {})
    res_files = p.scan()

    assert sorted(files) == sorted(res_files)


@pytest.mark.parametrize("fx", ["hive_fs_5"])
def test_hive_full_scan_with_fixed(request, fx):
    pattern, files, values = request.getfixturevalue(fx)

    v = {
        "shortName": values["shortName"],
    }

    p = HivePattern(pattern, v)
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
    pattern, _, _ = request.getfixturevalue(fx)

    # files = _build_fs(md, fs_pattern, date_format)
    # print(f"files={files}")

    p = HivePattern(pattern, {})
    res_files = p.scan(filters)

    # print(f"res_files={res_files}")

    assert sorted(expected_files) == sorted(res_files)


class HiveDiag:
    def __init__(self):
        self.file_count = 0
        self.sel_count = 0

    def file(self, count):
        self.file_count += count

    def sel(self, count):
        self.sel_count += count

    def reset(self):
        self.file_count = 0
        self.sel_count = 0


def test_hive_sel_1():
    root = earthkit_test_data_file("pattern/1")
    pattern = "{shortName}_{date:date(%Y-%m-%dT-H-%M)}_{step}.grib"

    ds = from_source("file-pattern", os.path.join(root, pattern), hive_partitioning=True)

    # assert ds.root == path
    diag = HiveDiag()
    # using hive partitioning keys
    r = ds.sel(shortName="t", step=12, _hive_diag=diag)
    assert diag.file_count == 1
    assert diag.sel_count == 0
    assert len(r) == 6

    md_ref = [("t", 1000, 12), ("t", 850, 12), ("t", 700, 12), ("t", 500, 12), ("t", 400, 12), ("t", 300, 12)]
    assert r.metadata("shortName", "level", "step") == md_ref

    # using hive partitioning keys + extra keys from GRIB header
    diag.reset()
    r = ds.sel(shortName="t", step=12, levtype="pl", _hive_diag=diag)
    assert diag.file_count == 1
    assert diag.sel_count == 1
    assert len(r) == 6


def test_hive_sel_2():
    root = earthkit_test_data_file("pattern/invalid")
    pattern = "_{shortName}_{date:date(%Y-%m-%dT%H:%M)}_{step}.grib"

    ds = from_source("file-pattern", os.path.join(root, pattern), hive_partitioning=True)

    r = ds.sel(shortName="t", step=12)
    assert len(r) == 0


def test_hive_init_1():
    pattern = "{shortName}_{date:date(%Y-%m-%dT%H:%M)}_{step}.grib"
    p = HivePattern(pattern)

    assert p.pattern == pattern
    assert p.params == ["shortName", "date", "step"]
    assert p.dynamic_params == ["shortName", "date", "step"]
    assert p.fixed_single_params == {}
    assert p.fixed_multi_params == {}
    assert p.root == ""
    assert p.rest == pattern

    assert len(p.parts) == 1
    ref = ["shortName", "date", "step"]
    for i, v in enumerate(p.parts[0].variables):
        assert v.name == ref[i]


def test_hive_init_2():
    pattern = "root_d/{year}/fc/t_{level}b_/a{shortName}_{date:date(%Y-%m-%dT%H:%M)}_{step}.grib"
    p = HivePattern(pattern)

    assert p.pattern == pattern
    assert p.params == ["year", "level", "shortName", "date", "step"]
    assert p.dynamic_params == ["year", "level", "shortName", "date", "step"]
    assert p.fixed_single_params == {}
    assert p.fixed_multi_params == {}
    assert p.root == "root_d"
    assert p.rest == pattern[7:]

    assert len(p.parts) == 4
    ref = [["year"], [], ["level"], ["shortName", "date", "step"]]
    for i, part in enumerate(p.parts):
        assert len(part.variables) == len(ref[i])
        for k, v in enumerate(part.variables):
            assert v.name == ref[i][k]

    ref = [False, True, False, False]
    for i, part in enumerate(p.parts):
        assert part.is_constant() == ref[i]

    assert p.parts[0].match("2023")
    assert p.parts[0].match("2_2_3")
    assert p.parts[1].match("fc")
    assert not p.parts[1].match("an")
    assert p.parts[2].match("t_500_b_")
    assert not p.parts[2].match("t_500_b")
    assert not p.parts[2].match("500")

    m = p.parts[3].match("at2m_2023-01-21_345.grib")
    assert m is not None
    assert m.groupdict() == {"shortName": "t2m", "date": "2023-01-21", "step": "345"}

    m = p.parts[3].match("a_t2m_2023-01-21_345.grib")
    assert m is not None
    assert m.groupdict() == {"shortName": "_t2m", "date": "2023-01-21", "step": "345"}

    m = p.parts[3].match("at2m2023-01-21_345.grib")
    assert m is None


def test_hive_init_3():
    pattern = "root_d/{year}/fc/t_{level}b_/a{shortName}_{date:date(%Y-%m-%dT%H:%M)}_{step}.grib"
    p = HivePattern(pattern, {"year": [2023, 2024], "level": "500", "shortName": "t"})

    assert p.pattern == pattern
    assert set(p.params) == {"year", "level", "shortName", "date", "step"}
    assert p.dynamic_params == ["date", "step"]
    assert p.fixed_single_params == {"level": "500", "shortName": "t"}
    assert p.fixed_multi_params == {"year": [2023, 2024]}
    assert p.root == "root_d"
    assert p.rest == "{year}/fc/t_500b_/at_{date:date(%Y-%m-%dT%H:%M)}_{step}.grib"

    assert len(p.parts) == 4
    ref = [["year"], [], [], ["date", "step"]]
    for i, part in enumerate(p.parts):
        assert len(part.variables) == len(ref[i])
        for k, v in enumerate(part.variables):
            assert v.name == ref[i][k]

    ref = [False, True, True, False]
    for i, part in enumerate(p.parts):
        assert part.is_constant() == ref[i]

    assert p.parts[0].match("2023")
    assert p.parts[0].match("2024")
    assert p.parts[0].match("2025")
    assert p.parts[0].match("2_2_3")
    assert p.parts[1].match("fc")
    assert not p.parts[1].match("an")
    assert p.parts[2].match("t_500b_")
    assert not p.parts[2].match("at_500b_")
    assert not p.parts[2].match("t_500b__")
    assert not p.parts[2].match("t_500_b")
    assert not p.parts[2].match("500")

    m = p.parts[3].match("at_2023-01-21_345.grib")
    assert m is not None
    assert m.groupdict() == {"date": "2023-01-21", "step": "345"}

    m = p.parts[3].match("a_t_2023-01-21_345.grib")
    assert m is None

    m = p.parts[3].match("at2023-01-21_345.grib")
    assert m is None
