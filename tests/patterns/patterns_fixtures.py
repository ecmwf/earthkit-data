# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime

import pytest


@pytest.fixture
def hive_fs_1(fs):
    pattern = "/my_root/{shortName}_{date:date(%Y-%m-%d)}+{step}.grib"
    values = {
        "shortName": ["t", "z", "r"],
        "date": [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 12)],
        "step": [0, 6, 12],
    }
    sample = "/my_root/r_2020-05-11+6.grib"
    num = 18

    return build_hive_fs(pattern, values, sample, num, fs)


@pytest.fixture
def hive_fs_2(fs):
    pattern = "/my_root/{shortName}/{date:date(%Y-%m-%d)}:{step}.grib"
    values = {
        "shortName": ["t", "z", "r"],
        "date": [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 12)],
        "step": [0, 6, 12],
    }
    sample = "/my_root/r/2020-05-11:6.grib"
    num = 18

    return build_hive_fs(pattern, values, sample, num, fs)


@pytest.fixture
def hive_fs_3(fs):
    pattern = "/my_root/{step}__/{shortName}/my+{date:date(%Y-%m-%d)}.grib"
    values = {
        "shortName": ["t", "z", "r"],
        "date": [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 12)],
        "step": [0, 6, 12],
    }
    sample = "/my_root/6__/r/my+2020-05-11.grib"
    num = 18

    return build_hive_fs(pattern, values, sample, num, fs)


@pytest.fixture
def hive_fs_4(fs):
    pattern = "/my_root/{step}__/{shortName}/{shortName}_{date:date(%Y-%m-%d)}.grib"
    values = {
        "shortName": ["t", "z", "r"],
        "date": [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 12)],
        "step": [0, 6, 12],
    }
    sample = "/my_root/6__/r/r_2020-05-11.grib"
    num = 18

    return build_hive_fs(pattern, values, sample, num, fs)


@pytest.fixture
def hive_fs_5(fs):
    pattern = "/my_root/{step}/{shortName}/{date:date(%Y-%m-%d)}.grib"
    values = {
        "shortName": "t",
        "date": [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 12)],
        "step": [0, 6, 12],
    }
    sample = "/my_root/0/t/2020-05-11.grib"
    num = 6

    return build_hive_fs(pattern, values, sample, num, fs)


def build_hive_fs(pattern, values, sample, file_num, fs):
    from earthkit.data.utils.patterns import Pattern

    p = Pattern(pattern)
    files = p.substitute(values)
    assert len(files) == file_num
    assert sample in files

    for f in files:
        fs.create_file(f)

    return pattern, files, values
