#!/usr/bin/env python3

# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import datetime
import os
import sys

import pandas as pd
import pytest

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_FILE  # noqa: E402
from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


def _check_ls_df(df, expected_values):
    df_ref = pd.DataFrame.from_dict(expected_values)
    df_ref.reset_index(drop=True, inplace=True)
    pd.testing.assert_frame_equal(
        df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
    )


@pytest.mark.skip(reason="to be revisited")
@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_describe(fl_type):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    # full contents
    df = f.describe()
    df = df.data

    ref = {
        "level": {
            ("t", "isobaricInhPa"): "1000,300,...",
            ("u", "isobaricInhPa"): "1000,300,...",
            ("v", "isobaricInhPa"): "1000,300,...",
        },
        "date": {
            ("t", "isobaricInhPa"): "20180801",
            ("u", "isobaricInhPa"): "20180801",
            ("v", "isobaricInhPa"): "20180801",
        },
        "time": {
            ("t", "isobaricInhPa"): "1200",
            ("u", "isobaricInhPa"): "1200",
            ("v", "isobaricInhPa"): "1200",
        },
        "stepRange": {
            ("t", "isobaricInhPa"): "0",
            ("u", "isobaricInhPa"): "0",
            ("v", "isobaricInhPa"): "0",
        },
        "paramId": {
            ("t", "isobaricInhPa"): "130",
            ("u", "isobaricInhPa"): "131",
            ("v", "isobaricInhPa"): "132",
        },
        "class": {
            ("t", "isobaricInhPa"): "od",
            ("u", "isobaricInhPa"): "od",
            ("v", "isobaricInhPa"): "od",
        },
        "stream": {
            ("t", "isobaricInhPa"): "oper",
            ("u", "isobaricInhPa"): "oper",
            ("v", "isobaricInhPa"): "oper",
        },
        "type": {
            ("t", "isobaricInhPa"): "an",
            ("u", "isobaricInhPa"): "an",
            ("v", "isobaricInhPa"): "an",
        },
        "experimentVersionNumber": {
            ("t", "isobaricInhPa"): "0001",
            ("u", "isobaricInhPa"): "0001",
            ("v", "isobaricInhPa"): "0001",
        },
    }

    assert ref == df.to_dict()

    # repeated use
    df = f.describe()
    df = df.data
    assert ref == df.to_dict()

    # single param by shortName
    df = f.describe("t")
    df = df.data

    ref = {
        0: {
            "shortName": "t",
            "typeOfLevel": "isobaricInhPa",
            "level": "1000,300,400,850,500,700",
            "date": "20180801",
            "time": "1200",
            "stepRange": "0",
            "paramId": "130",
            "class": "od",
            "stream": "oper",
            "type": "an",
            "experimentVersionNumber": "0001",
        }
    }

    assert ref[0] == df[0].to_dict()

    # repeated use
    df = f.describe(param="t")
    df = df.data
    assert ref[0] == df[0].to_dict()

    df = f.describe("t")
    df = df.data
    assert ref[0] == df[0].to_dict()

    df = f.describe(param="t")
    df = df.data
    assert ref[0] == df[0].to_dict()

    # single param by paramId
    df = f.describe(130)
    df = df.data

    ref = {
        0: {
            "shortName": "t",
            "typeOfLevel": "isobaricInhPa",
            "level": "1000,300,400,850,500,700",
            "date": "20180801",
            "time": "1200",
            "stepRange": "0",
            "paramId": "130",
            "class": "od",
            "stream": "oper",
            "type": "an",
            "experimentVersionNumber": "0001",
        }
    }

    assert ref[0] == df[0].to_dict()

    df = f.describe(param=130)
    df = df.data
    assert ref[0] == df[0].to_dict()


# @pytest.mark.skip(reason="to be revisited")
# # @pytest.mark.parametrize("fl_type", FL_TYPES)
# @pytest.mark.parametrize("fl_type", ["file"])
# def test_grib_describe_field(fl_type):
#     f_in, _ = load_grib_data("tuv_pl.grib", fl_type)
#     f = f_in[0]

#     # full contents
#     df = f.describe()
#     assert i
#     df = df.data

#     ref = {
#         "level": {("t", "isobaricInhPa"): "1000"},
#         "date": {("t", "isobaricInhPa"): "20180801"},
#         "time": {("t", "isobaricInhPa"): "1200"},
#         "stepRange": {("t", "isobaricInhPa"): "0"},
#         "paramId": {("t", "isobaricInhPa"): "130"},
#         "class": {("t", "isobaricInhPa"): "od"},
#         "stream": {("t", "isobaricInhPa"): "oper"},
#         "type": {("t", "isobaricInhPa"): "an"},
#         "experimentVersionNumber": {("t", "isobaricInhPa"): "0001"},
#     }

#     assert ref == df.to_dict()

#     # repeated use
#     df = f.describe()
#     df = df.data
#     assert ref == df.to_dict()


# TODO: test with default keys once established
@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_kwargs,expected_values",
    [
        (
            {
                "keys": [
                    "parameter.variable",
                    "vertical.level_type",
                    "vertical.level",
                    "time.base_datetime",
                    "time.valid_datetime",
                    "time.step",
                    "ensemble.member",
                ]
            },
            {
                "parameter.variable": {0: "t", 1: "u", 2: "v", 3: "t"},
                "vertical.level_type": {
                    0: "pressure",
                    1: "pressure",
                    2: "pressure",
                    3: "pressure",
                },
                "vertical.level": {0: 1000, 1: 1000, 2: 1000, 3: 850},
                "time.base_datetime": {
                    0: datetime.datetime(2018, 8, 1, 12),
                    1: datetime.datetime(2018, 8, 1, 12),
                    2: datetime.datetime(2018, 8, 1, 12),
                    3: datetime.datetime(2018, 8, 1, 12),
                },
                "time.valid_datetime": {
                    0: datetime.datetime(2018, 8, 1, 12),
                    1: datetime.datetime(2018, 8, 1, 12),
                    2: datetime.datetime(2018, 8, 1, 12),
                    3: datetime.datetime(2018, 8, 1, 12),
                },
                "time.step": {
                    0: datetime.timedelta(0),
                    1: datetime.timedelta(0),
                    2: datetime.timedelta(0),
                    3: datetime.timedelta(0),
                },
                "ensemble.member": {0: "0", 1: "0", 2: "0", 3: "0"},
            },
        ),
        (
            {
                "keys": [
                    "parameter.variable",
                    "vertical.level",
                ],
                "extra_keys": ["ensemble.member"],
            },
            {
                "parameter.variable": {0: "t", 1: "u", 2: "v", 3: "t"},
                "vertical.level": {0: 1000, 1: 1000, 2: 1000, 3: 850},
                "ensemble.member": {0: "0", 1: "0", 2: "0", 3: "0"},
            },
        ),
        (
            {
                "keys": [
                    "parameter.variable",
                    "vertical.level",
                ],
                "extra_keys": ["ensemble.member"],
            },
            {
                "parameter.variable": {0: "t", 1: "u", 2: "v", 3: "t"},
                "vertical.level": {0: 1000, 1: 1000, 2: 1000, 3: 850},
                "ensemble.member": {0: "0", 1: "0", 2: "0", 3: "0"},
            },
        ),
        (
            {
                "keys": [
                    "parameter.variable",
                    "metadata.levtype",
                ],
            },
            {
                "parameter.variable": {0: "t", 1: "u", 2: "v", 3: "t"},
                "metadata.levtype": {0: "pl", 1: "pl", 2: "pl", 3: "pl"},
            },
        ),
        (
            {
                "keys": [
                    "metadata.levtype",
                    "parameter.variable",
                ],
            },
            {
                "metadata.levtype": {0: "pl", 1: "pl", 2: "pl", 3: "pl"},
                "parameter.variable": {0: "t", 1: "u", 2: "v", 3: "t"},
            },
        ),
        ({"keys": ["_missing_key"]}, {"_missing_key": {0: None, 1: None, 2: None, 3: None}}),
    ],
)
def test_grib_ls_core(_kwargs, expected_values, fl_type):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    f1 = f[0:4]
    df = f1.ls(**_kwargs)

    _check_ls_df(df, expected_values)


# @pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize(
    "_kwargs,expected_values",
    [
        (
            {
                "n": 2,
                "keys": None,
                "collections": "parameter",
            },
            {
                "parameter.variable": {0: "t", 1: "u"},
                "parameter.units": {0: "kelvin", 1: "meter / second"},
            },
        ),
        (
            {
                "n": 2,
                "keys": None,
                "collections": "parameter",
                "extra_keys": ["vertical.level"],
            },
            {
                "parameter.variable": {0: "t", 1: "u"},
                "parameter.units": {0: "kelvin", 1: "meter / second"},
                "vertical.level": {0: 1000, 1: 1000},
            },
        ),
    ],
)
def test_grib_ls_component(_kwargs, expected_values, fl_type):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    df = f.ls(**_kwargs)
    assert expected_values == df.to_dict()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_args,_kwargs,expected_values",
    [
        (
            (2,),
            {
                "keys": [
                    "vertical.level",
                    "parameter.variable",
                ],
            },
            {
                "vertical.level": {0: 1000, 1: 1000},
                "parameter.variable": {
                    0: "t",
                    1: "u",
                },
            },
        ),
        (
            tuple(),
            {
                "n": 2,
                "keys": [
                    "vertical.level",
                    "parameter.variable",
                ],
            },
            {
                "vertical.level": {0: 1000, 1: 1000},
                "parameter.variable": {
                    0: "t",
                    1: "u",
                },
            },
        ),
        (
            (-2,),
            {
                "keys": [
                    "vertical.level",
                    "parameter.variable",
                ],
            },
            {
                "vertical.level": {0: 300, 1: 300},
                "parameter.variable": {
                    0: "u",
                    1: "v",
                },
            },
        ),
        (
            tuple(),
            {
                "n": -2,
                "keys": [
                    "vertical.level",
                    "parameter.variable",
                ],
            },
            {
                "vertical.level": {0: 300, 1: 300},
                "parameter.variable": {
                    0: "u",
                    1: "v",
                },
            },
        ),
    ],
)
def test_grib_ls_num(_args, _kwargs, expected_values, fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    df = ds.ls(*_args, **_kwargs)
    assert expected_values == df.to_dict()


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_ls_invalid_num(fl_type):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    with pytest.raises(ValueError):
        f.ls(n=0)

    with pytest.raises(ValueError):
        f.ls(0)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_ls_invalid_arg(fl_type):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)
    with pytest.raises(TypeError):
        f.ls(invalid=1)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_kwargs,expected_values",
    [
        (
            {"keys": ["parameter.variable", "vertical.level"]},
            {"parameter.variable": {0: "t"}, "vertical.level": {0: 1000}},
        ),
        (
            {"keys": ["parameter.variable", "vertical.level"], "extra_keys": ["ensemble.member"]},
            {"parameter.variable": {0: "t"}, "vertical.level": {0: 1000}, "ensemble.member": {0: "0"}},
        ),
        (
            {"keys": ["parameter.variable", "vertical.level", "metadata.levtype"]},
            {"parameter.variable": {0: "t"}, "vertical.level": {0: 1000}, "metadata.levtype": {0: "pl"}},
        ),
    ],
)
def test_grib_ls_single_field(_kwargs, expected_values, fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    f = ds[0]
    df = f.ls(**_kwargs)
    assert expected_values == df.to_dict()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_kwargs,expected_values",
    [
        (
            {
                "keys": [
                    "metadata.centre",
                    "metadata.shortName",
                    "metadata.typeOfLevel",
                    "metadata.level",
                    "metadata.dataDate",
                    "metadata.dataTime",
                    "metadata.stepRange",
                    "metadata.dataType",
                    "metadata.number",
                    "metadata.gridType",
                ]
            },
            {
                "metadata.centre": {0: "ecmf", 1: "ecmf", 2: "ecmf", 3: "ecmf"},
                "metadata.shortName": {0: "t", 1: "u", 2: "v", 3: "t"},
                "metadata.typeOfLevel": {
                    0: "isobaricInhPa",
                    1: "isobaricInhPa",
                    2: "isobaricInhPa",
                    3: "isobaricInhPa",
                },
                "metadata.level": {0: 1000, 1: 1000, 2: 1000, 3: 850},
                "metadata.dataDate": {0: 20180801, 1: 20180801, 2: 20180801, 3: 20180801},
                "metadata.dataTime": {0: 1200, 1: 1200, 2: 1200, 3: 1200},
                "metadata.stepRange": {0: "0", 1: "0", 2: "0", 3: "0"},
                "metadata.dataType": {0: "an", 1: "an", 2: "an", 3: "an"},
                "metadata.number": {0: 0, 1: 0, 2: 0, 3: 0},
                "metadata.gridType": {
                    0: "regular_ll",
                    1: "regular_ll",
                    2: "regular_ll",
                    3: "regular_ll",
                },
            },
        ),
        (
            {
                "keys": [
                    "metadata.centre",
                    "metadata.shortName",
                ],
                "extra_keys": [
                    "metadata.typeOfLevel",
                ],
            },
            {
                "metadata.centre": {0: "ecmf", 1: "ecmf", 2: "ecmf", 3: "ecmf"},
                "metadata.shortName": {0: "t", 1: "u", 2: "v", 3: "t"},
                "metadata.typeOfLevel": {
                    0: "isobaricInhPa",
                    1: "isobaricInhPa",
                    2: "isobaricInhPa",
                    3: "isobaricInhPa",
                },
            },
        ),
        (
            {"keys": ["metadata._missing_key"]},
            {"metadata._missing_key": {0: None, 1: None, 2: None, 3: None}},
        ),
        (
            {"keys": ["metadata._missing_key", "_missing_key"]},
            {
                "metadata._missing_key": {0: None, 1: None, 2: None, 3: None},
                "_missing_key": {0: None, 1: None, 2: None, 3: None},
            },
        ),
    ],
)
def test_grib_ls_ecc_core(_kwargs, expected_values, fl_type):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    f1 = f[0:4]
    df = f1.ls(**_kwargs)

    assert expected_values == df.to_dict()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_kwargs,expected_values",
    [
        (
            {
                "n": 2,
                "keys": None,
                "collections": "metadata.vertical",
            },
            {
                "metadata.vertical.typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
                "metadata.vertical.level": {0: 1000, 1: 1000},
            },
        ),
        (
            {
                "n": 2,
                "keys": None,
                "collections": "metadata.vertical",
                "extra_keys": ["metadata.shortName"],
            },
            {
                "metadata.vertical.typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
                "metadata.vertical.level": {0: 1000, 1: 1000},
                "metadata.shortName": {0: "t", 1: "u"},
            },
        ),
    ],
)
def test_grib_ls_ecc_namespace(_kwargs, expected_values, fl_type):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    df = f.ls(**_kwargs)
    assert df.to_dict() == expected_values


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_args,_kwargs,expected_values",
    [
        (
            (2,),
            {
                "keys": [
                    "metadata.level",
                    "metadata.shortName",
                ],
            },
            {
                "metadata.level": {0: 1000, 1: 1000},
                "metadata.shortName": {
                    0: "t",
                    1: "u",
                },
            },
        ),
        (
            tuple(),
            {
                "n": 2,
                "keys": [
                    "metadata.level",
                    "metadata.shortName",
                ],
            },
            {
                "metadata.level": {0: 1000, 1: 1000},
                "metadata.shortName": {
                    0: "t",
                    1: "u",
                },
            },
        ),
        (
            (-2,),
            {
                "keys": [
                    "metadata.level",
                    "metadata.shortName",
                ],
            },
            {
                "metadata.level": {0: 300, 1: 300},
                "metadata.shortName": {
                    0: "u",
                    1: "v",
                },
            },
        ),
        (
            tuple(),
            {
                "n": -2,
                "keys": [
                    "metadata.level",
                    "metadata.shortName",
                ],
            },
            {
                "metadata.level": {0: 300, 1: 300},
                "metadata.shortName": {
                    0: "u",
                    1: "v",
                },
            },
        ),
    ],
)
def test_grib_ls_ecc_num(_args, _kwargs, expected_values, fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    df = ds.ls(*_args, **_kwargs)
    assert expected_values == df.to_dict()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_kwargs,expected_values",
    [
        (
            {"keys": ["metadata.shortName", "metadata.level"]},
            {"metadata.shortName": {0: "t"}, "metadata.level": {0: 1000}},
        ),
        (
            {"keys": ["metadata.shortName", "metadata.level"], "extra_keys": ["metadata.typeOfLevel"]},
            {
                "metadata.shortName": {0: "t"},
                "metadata.level": {0: 1000},
                "metadata.typeOfLevel": {0: "isobaricInhPa"},
            },
        ),
    ],
)
def test_grib_ls_ecc_single_field(_kwargs, expected_values, fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    f = ds[0]
    df = f.ls(**_kwargs)
    assert expected_values == df.to_dict()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_args,_kwargs,expected_values",
    [
        (
            (2,),
            {
                "keys": [
                    "vertical.level",
                    "parameter.variable",
                ],
            },
            {
                "vertical.level": {0: 1000, 1: 1000},
                "parameter.variable": {
                    0: "t",
                    1: "u",
                },
            },
        ),
        (
            tuple(),
            {
                "n": 2,
                "keys": [
                    "vertical.level",
                    "parameter.variable",
                ],
            },
            {
                "vertical.level": {0: 1000, 1: 1000},
                "parameter.variable": {
                    0: "t",
                    1: "u",
                },
            },
        ),
    ],
)
def test_grib_head_num(_args, _kwargs, expected_values, fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    df = ds.head(*_args, **_kwargs)
    assert expected_values == df.to_dict()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_args,_kwargs,expected_values",
    [
        (
            (2,),
            {
                "keys": [
                    "vertical.level",
                    "parameter.variable",
                ],
            },
            {
                "vertical.level": {0: 300, 1: 300},
                "parameter.variable": {
                    0: "u",
                    1: "v",
                },
            },
        ),
        (
            tuple(),
            {
                "n": 2,
                "keys": [
                    "vertical.level",
                    "parameter.variable",
                ],
            },
            {
                "vertical.level": {0: 300, 1: 300},
                "parameter.variable": {
                    0: "u",
                    1: "v",
                },
            },
        ),
    ],
)
def test_grib_tail_num(_args, _kwargs, expected_values, fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    df = ds.tail(*_args, **_kwargs)
    assert expected_values == df.to_dict()


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_describe_field_1(fl_type):
    f, _ = load_grib_data("test6.grib", fl_type)

    components = (
        "parameter",
        "time",
        "vertical",
    )

    # default
    r = f[0].describe(component=components, _as_raw=True)
    ref = [
        {
            "title": "parameter",
            "data": {
                "variable": "t",
                "units": "kelvin",
            },
            "tooltip": "Keys in the parameter namespace",
        },
        {
            "title": "time",
            "data": {
                "base_datetime": datetime.datetime(2018, 8, 1, 12),
                "valid_datetime": datetime.datetime(2018, 8, 1, 12),
                "step": datetime.timedelta(0),
            },
            "tooltip": "Keys in the time namespace",
        },
        {
            "title": "vertical",
            "data": {
                "level": 1000,
                "level_type": "pressure",
            },
            "tooltip": "Keys in the vertical namespace",
        },
    ]

    assert len(r) == len(components)
    assert isinstance(r, list)
    for d in r:
        part = d["title"]
        assert part in components
        d_ref = [x for x in ref if x["title"] == part][0]
        assert d["tooltip"] == d_ref["tooltip"], part
        for k, v in d_ref["data"].items():
            assert d["data"][k] == v, f"{part}: key={k}"


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_describe_field_ecc_1(fl_type):
    f, _ = load_grib_data("test6.grib", fl_type)

    namespaces = (
        "geography",
        "ls",
        "mars",
        "parameter",
        "statistics",
        "time",
        "vertical",
    )

    # default
    r = f[0].describe(component="metadata", filter=namespaces, _as_raw=True)
    ref = [
        {
            "title": "ls",
            "data": {
                "edition": 1,
                "centre": "ecmf",
            },
            "tooltip": "Keys in the ls namespace",
        },
        {
            "title": "geography",
            "data": {
                "gridType": "regular_ll",
            },
            "tooltip": "Keys in the geography namespace",
        },
        {
            "title": "mars",
            "data": {
                "levtype": "pl",
            },
            "tooltip": "Keys in the mars namespace",
        },
        {
            "title": "parameter",
            "data": {
                "shortName": "t",
            },
            "tooltip": "Keys in the parameter namespace",
        },
        {
            "title": "time",
            "data": {
                "dataDate": 20180801,
            },
            "tooltip": "Keys in the time namespace",
        },
        {
            "title": "vertical",
            "data": {"typeOfLevel": "isobaricInhPa"},
            "tooltip": "Keys in the vertical namespace",
        },
    ]

    assert len(r) == len(namespaces)
    assert isinstance(r, list)
    for d in r:
        ns = d["title"]
        assert ns in namespaces
        assert d["data"], ns
        if ns not in ("default", "statistics"):
            d_ref = [x for x in ref if x["title"] == ns][0]
            assert d["tooltip"] == d_ref["tooltip"], ns
            for k, v in d_ref["data"].items():
                assert d["data"][k] == v, f"{ns}: key={k}"
        else:
            assert d["tooltip"], ns


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_describe_field_ecc_2(fl_type):
    f, _ = load_grib_data("test6.grib", fl_type)

    r = f[0].describe(component="metadata", filter="mars", _as_raw=True)
    ref = [
        {
            "title": "mars",
            "data": {
                "step": 0,
                "param": "t",
            },
            "tooltip": "Keys in the mars namespace",
        }
    ]

    assert len(r) == len(ref)
    assert r[0]["title"] == ref[0]["title"]
    for k, v in ref[0]["data"].items():
        assert r[0]["data"][k] == v, f"key={k}"
    assert r[0]["tooltip"] == ref[0]["tooltip"]


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_describe_field_ecc_3(fl_type):
    f, _ = load_grib_data("test6.grib", fl_type)

    r = f[0].describe(component="metadata", filter="mars", _as_raw=False)

    ref = {
        "mars": {
            "step": 0,
            "param": "t",
        }
    }

    assert len(r) == len(ref)
    d = r["mars"]
    d_ref = ref["mars"]

    for k, v in d_ref.items():
        assert d[k] == v, f"key={k}, value={d[k]}, ref={v}"


# @pytest.mark.parametrize(
#     "_args,_kwargs,expected_values",
#     [
#         (("vertical",), {}, {"level": 1000, "level_type": "pressure", "units": "hPa"}),
#         (
#             ("vertical",),
#             {"unwrap_single": False},
#             {"vertical": {"level": 1000, "level_type": "pressure", "units": "hPa"}},
#         ),
#         (
#             (
#                 [
#                     "vertical",
#                     "time",
#                 ],
#             ),
#             {},
#             {
#                 "vertical": {"level": 1000, "level_type": "pressure", "units": "hPa"},
#                 "time": {
#                     "base_datetime": datetime.datetime(2018, 8, 1, 12, 0),
#                     "step": datetime.timedelta(0),
#                     "valid_datetime": datetime.datetime(2018, 8, 1, 12, 0),
#                 },
#             },
#         ),
#     ],
# )
# @pytest.mark.parametrize("fl_type", FL_FILE)
# def test_grib_namespace_1(_args, _kwargs, expected_values, fl_type):
#     f, _ = load_grib_data("test6.grib", fl_type)

#     r = f[0].namespace(*_args, **_kwargs)
#     assert r == expected_values
#     return


# @pytest.mark.parametrize(
#     "_args",
#     [tuple(), (all,), ([all],), ("all",), (["all"],)],
# )
# @pytest.mark.parametrize("fl_type", FL_FILE)
# def test_grib_get_namespace_all(_args, fl_type):
#     f, _ = load_grib_data("test6.grib", fl_type)

#     r = f[0].namespace(*_args)
#     assert isinstance(r, dict)
#     assert set(r.keys()) == {"parameter", "time", "vertical", "geography", "ensemble", "proc"}

#     for k, v in r.items():
#         assert isinstance(v, dict), f"key={k} type={type(v)}"
#         if k not in ["geography", "proc"]:  # geography and proc can be empty
#             assert len(v) > 0, f"key={k} is empty"


# @pytest.mark.parametrize(
#     "_args,_kwargs,expected_values",
#     [
#         (("grib.vertical",), {}, {"grib.typeOfLevel": "isobaricInhPa", "grib.level": 1000}),
#         (
#             ("grib.vertical",),
#             {"simplify": False},
#             {"grib.vertical": {"grib.typeOfLevel": "isobaricInhPa", "grib.level": 1000}},
#         ),
#         (
#             (
#                 [
#                     "grib.vertical",
#                     "grib.time",
#                 ],
#             ),
#             {},
#             {
#                 "grib.vertical": {"grib.typeOfLevel": "isobaricInhPa", "grib.level": 1000},
#                 "grib.time": {
#                     "grib.dataDate": 20180801,
#                     "grib.dataTime": 1200,
#                     "grib.stepUnits": 1,
#                     "grib.stepType": "instant",
#                     "grib.stepRange": "0",
#                     "grib.startStep": 0,
#                     "grib.endStep": 0,
#                     "grib.validityDate": 20180801,
#                     "grib.validityTime": 1200,
#                 },
#             },
#         ),
#     ],
# )
# @pytest.mark.parametrize("fl_type", FL_FILE)
# def test_grib_namespace_ecc_1(_args, _kwargs, expected_values, fl_type):
#     f, _ = load_grib_data("test6.grib", fl_type)

#     r = f[0].namespace(*_args, **_kwargs)
#     for k, v in expected_values.items():
#         if isinstance(v, dict):
#             for kk, vv in v.items():
#                 assert r[k][kk] == vv, f"key={k}.{kk}"
#         else:
#             assert r[k] == v, f"key={k}"
#     return


# @pytest.mark.parametrize("fl_type", FL_FILE)
# def test_grib_ecc_namespace_all(fl_type):
#     f, _ = load_grib_data("test6.grib", fl_type)

#     r = f[0].namespace("grib")
#     assert isinstance(r, dict)
#     ref = {
#         "grib.geography",
#         "grib.statistics",
#         "grib.vertical",
#         "grib.time",
#         "grib.parameter",
#         "grib.mars",
#         "grib.ls",
#     }
#     assert set(r.keys()) == ref

#     for k, v in r.items():
#         assert isinstance(v, dict), f"key={k} type={type(v)}"
#         assert len(v) > 0, f"key={k} is empty"


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    # test_datetime()
    main(__file__)
