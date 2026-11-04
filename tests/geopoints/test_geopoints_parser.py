#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import pandas as pd
import pytest

from earthkit.data.readers.geopoints.parser import parse_geopoints
from earthkit.data.utils.testing import earthkit_test_data_file


def _data_file(name):
    return earthkit_test_data_file("geopoints", name)


def _write(tmp_path, text, name="test.gpt"):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def _parse_block(tmp_path, text):
    f = parse_geopoints(_write(tmp_path, text))
    assert len(f.blocks) == 1
    return f.blocks[0]


def _ts(s):
    return np.datetime64(s, "ns")


# -- test data files --------------------------------------------------------------------------


def test_geopoints_parser_traditional():
    f = parse_geopoints(_data_file("traditional.gpt"))
    assert f.is_set is False
    assert len(f.blocks) == 1
    b = f.blocks[0]
    assert b.format == "TRADITIONAL"
    assert b.columns == ["latitude", "longitude", "level", "date", "time", "value"]
    assert b.metadata == {}

    df = b.to_pandas()
    assert list(df.columns) == ["latitude", "longitude", "level", "date", "value"]
    assert len(df) == 8
    for c in ["latitude", "longitude", "level", "value"]:
        assert df[c].dtype == np.float64
    assert df["date"].dtype == np.dtype("datetime64[ns]")

    r = df.iloc[0]
    assert r["latitude"] == 36.15
    assert r["longitude"] == -5.35
    assert r["level"] == 0.0
    assert r["date"] == _ts("2010-08-10T12:00")
    assert r["value"] == 300.9

    # 3e+38 is the missing value
    assert np.isnan(df["value"].iloc[4])
    assert df["value"].iloc[3] == 294.8
    assert df["value"].isna().sum() == 1


def test_geopoints_parser_to_pandas_returns_new_frame():
    b = parse_geopoints(_data_file("traditional.gpt")).blocks[0]
    df1 = b.to_pandas()
    df1.loc[0, "value"] = -1
    df2 = b.to_pandas()
    assert df2["value"].iloc[0] == 300.9


def test_geopoints_parser_xyv():
    b = parse_geopoints(_data_file("xyv.gpt")).blocks[0]
    assert b.format == "XYV"
    assert b.columns == ["longitude", "latitude", "value"]

    df = b.to_pandas()
    assert list(df.columns) == ["longitude", "latitude", "value"]
    assert len(df) == 4
    assert all(df[c].dtype == np.float64 for c in df.columns)
    r = df.iloc[0]
    assert (r["longitude"], r["latitude"], r["value"]) == (-5.35, 36.15, 300.9)
    assert df["value"].iloc[3] == 300.4


def test_geopoints_parser_xy_vector():
    b = parse_geopoints(_data_file("xy_vector.gpt")).blocks[0]
    assert b.format == "XY_VECTOR"
    assert b.columns == ["latitude", "longitude", "level", "date", "time", "x-comp", "y-comp"]

    df = b.to_pandas()
    assert list(df.columns) == ["latitude", "longitude", "level", "date", "x-comp", "y-comp"]
    assert len(df) == 3
    r = df.iloc[0]
    assert r["latitude"] == 80.0
    assert r["longitude"] == 0.0
    assert r["level"] == 0.0
    assert r["date"] == _ts("2003-06-17T12:00")
    assert r["x-comp"] == -4.9001
    assert r["y-comp"] == -8.3126
    assert df["longitude"].tolist() == [0.0, 5.5, 11.0]
    assert df["y-comp"].iloc[2] == -7.13829


def test_geopoints_parser_polar_vector():
    b = parse_geopoints(_data_file("polar_vector.gpt")).blocks[0]
    assert b.format == "POLAR_VECTOR"
    assert b.columns == ["latitude", "longitude", "level", "date", "time", "magnitude", "angle"]

    df = b.to_pandas()
    assert list(df.columns) == ["latitude", "longitude", "level", "date", "magnitude", "angle"]
    assert len(df) == 3
    r = df.iloc[0]
    assert (r["latitude"], r["longitude"], r["level"]) == (50.97, 6.05, 0.0)
    assert r["date"] == _ts("2003-06-14T12:00")
    assert (r["magnitude"], r["angle"]) == (4.0, 90.0)
    assert df["angle"].tolist() == [90.0, 330.0, 170.0]


def test_geopoints_parser_ncols_stnid():
    b = parse_geopoints(_data_file("ncols_stnid.gpt")).blocks[0]
    assert b.format == "NCOLS"
    assert b.columns == ["stnid", "latitude", "time", "longitude", "level", "date", "_v1", "_v2", "_v3"]

    df = b.to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "level", "date", "_v1", "_v2", "_v3"]
    assert len(df) == 4
    assert df["stnid"].dtype == object
    assert df["stnid"].tolist() == ["heathrow", "oxford", "texas", "aberdeen"]
    r = df.iloc[0]
    assert r["latitude"] == 32.55
    assert r["longitude"] == 35.85
    assert r["level"] == 10.0
    assert r["date"] == _ts("2012-02-18T06:00")
    assert (r["_v1"], r["_v2"], r["_v3"]) == (273.9, 29.0, 7.0)
    assert df["date"].iloc[1] == _ts("2012-02-18T18:00")
    assert df["_v3"].iloc[3] == 0.5
    for c in ["latitude", "longitude", "level", "_v1", "_v2", "_v3"]:
        assert df[c].dtype == np.float64


def test_geopoints_parser_ncols_docs_example():
    # D1: no stnid in the file, so a stnid column filled with None is added first
    b = parse_geopoints(_data_file("ncols.gpt")).blocks[0]
    assert b.format == "NCOLS"
    assert b.columns == ["stnid", "latitude", "longitude", "time", "date", "t2", "o3", "td", "rh"]

    df = b.to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "date", "t2", "o3", "td", "rh"]
    assert len(df) == 4
    assert df["stnid"].dtype == object
    assert all(v is None for v in df["stnid"])
    r = df.iloc[0]
    assert (r["latitude"], r["longitude"]) == (32.55, 35.85)
    assert r["date"] == _ts("2012-02-18T06:00")
    assert (r["t2"], r["o3"], r["td"], r["rh"]) == (273.9, 35.0, 280.3, 75.0)
    assert df["date"].tolist() == [
        pd.Timestamp("2012-02-18T06:00"),
        pd.Timestamp("2012-02-18T18:00"),
        pd.Timestamp("2014-02-18T12:00"),
        pd.Timestamp("2015-02-18T12:00"),
    ]
    assert df["rh"].tolist() == [75.0, 68.0, 34.0, 42.0]


def test_geopoints_parser_metadata():
    f = parse_geopoints(_data_file("metadata.gpt"))
    b = f.blocks[0]
    assert b.metadata == {"param": "temperature", "date": 20130804, "time": 1200, "level": 0.2}
    assert isinstance(b.metadata["date"], int)
    assert isinstance(b.metadata["time"], int)
    assert isinstance(b.metadata["level"], float)
    assert isinstance(b.metadata["param"], str)

    df = b.to_pandas()
    assert len(df) == 44
    r = df.iloc[0]
    assert (r["latitude"], r["longitude"], r["level"]) == (55.01, 8.41, 0.2)
    assert r["date"] == _ts("2013-08-04T12:00")
    assert r["value"] == 294.4


def test_geopoints_parser_missing_latlon():
    df = parse_geopoints(_data_file("missing_latlon.gpt")).blocks[0].to_pandas()
    assert len(df) == 7
    assert list(df.columns) == ["latitude", "longitude", "level", "date", "value"]
    assert df["latitude"].dtype == np.float64

    r = df.iloc[0]
    assert (r["latitude"], r["longitude"], r["level"], r["value"]) == (54.33, 8.6, 0.2, 100.0)
    assert r["date"] == _ts("2013-08-04T12:00")

    assert np.isnan(df["latitude"].iloc[1])
    assert df["longitude"].iloc[1] == 8.8
    assert df["date"].iloc[1] == _ts("2013-08-04T14:00")
    assert df["latitude"].iloc[3] == 47.88
    assert np.isnan(df["longitude"].iloc[3])
    assert np.isnan(df["latitude"].iloc[5])
    assert np.isnan(df["longitude"].iloc[5])
    assert df["date"].iloc[5] == _ts("2017-08-14T09:00")
    assert df["latitude"].isna().tolist() == [False, True, False, False, False, True, False]
    assert df["value"].isna().sum() == 0


def test_geopoints_parser_geopointset():
    f = parse_geopoints(_data_file("geopointset.gpts"))
    assert f.is_set is True
    assert len(f.blocks) == 3
    assert [b.metadata for b in f.blocks] == [{}, {"param": "geopotential"}, {}]
    assert [len(b.to_pandas()) for b in f.blocks] == [4, 1, 3]
    assert all(b.format == "TRADITIONAL" for b in f.blocks)

    df = f.blocks[1].to_pandas()
    r = df.iloc[0]
    assert (r["latitude"], r["longitude"], r["level"]) == (60.82, 23.5, 0.0)
    assert r["date"] == _ts("2013-05-12T06:00")
    assert r["value"] == 101045.8

    df = f.blocks[0].to_pandas()
    assert df["date"].iloc[0] == _ts("2013-05-12T00:00")
    assert df["value"].iloc[0] == 100869.8625

    df = f.blocks[2].to_pandas()
    assert df["date"].iloc[0] == _ts("2013-05-13T00:00")
    assert df["value"].iloc[2] == 100846.619


def test_geopoints_parser_empty_set(tmp_path):
    f = parse_geopoints(_write(tmp_path, "#GEOPOINTSET\n"))
    assert f.is_set is True
    assert f.blocks == []


def test_geopoints_parser_plain_geo_is_not_set(tmp_path):
    f = parse_geopoints(_write(tmp_path, "#GEO\n#DATA\n1 2 0 20200101 1200 5\n"))
    assert f.is_set is False
    assert len(f.blocks) == 1
    assert len(f.blocks[0].to_pandas()) == 1


def test_geopoints_parser_set_blocks_with_different_formats(tmp_path):
    f = parse_geopoints(
        _write(
            tmp_path,
            "#GEOPOINTSET\n"
            "#GEO\n#FORMAT XYV\n#DATA\n10 20 5\n"
            "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude t2\n#DATA\n1 2 3\n4 5 6\n",
        )
    )
    assert [b.format for b in f.blocks] == ["XYV", "NCOLS"]
    assert list(f.blocks[0].to_pandas().columns) == ["longitude", "latitude", "value"]
    assert list(f.blocks[1].to_pandas().columns) == ["stnid", "latitude", "longitude", "t2"]


# -- missing values -----------------------------------------------------------------------------


def test_geopoints_parser_missing_in_xy_vector(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT XY_VECTOR\n#DATA\n"
        "10 20 0 20200101 1200 3e38 1.5\n"
        "11 21 0 20200101 1200 2.5 3.0E+38\n"
        "12 22 0 20200101 1200 3e+38 3e38\n",
    )
    df = b.to_pandas()
    assert df["x-comp"].isna().tolist() == [True, False, True]
    assert df["y-comp"].isna().tolist() == [False, True, True]
    assert df["x-comp"].iloc[1] == 2.5
    assert df["y-comp"].iloc[0] == 1.5


@pytest.mark.parametrize(
    "spelling", ["3e38", "3e+38", "3.0E+38", "3.0e38", "3E38", "300000000000000000000000000000000000000"]
)
def test_geopoints_parser_missing_spellings(tmp_path, spelling):
    b = _parse_block(tmp_path, f"#GEO\n#DATA\n{spelling} {spelling} {spelling} {spelling} {spelling} {spelling}\n")
    df = b.to_pandas()
    for c in ["latitude", "longitude", "level", "value"]:
        assert np.isnan(df[c].iloc[0]), c
    assert pd.isna(df["date"].iloc[0])


def test_geopoints_parser_missing_in_ncols_and_xyv(tmp_path):
    b = _parse_block(tmp_path, "#GEO\n#FORMAT NCOLS\n#COLUMNS\nstnid latitude longitude t2\n#DATA\nabc 3e38 4 3e+38\n")
    df = b.to_pandas()
    assert np.isnan(df["latitude"].iloc[0])
    assert df["longitude"].iloc[0] == 4.0
    assert np.isnan(df["t2"].iloc[0])

    b = _parse_block(tmp_path, "#GEO\n#FORMAT XYV\n#DATA\n3e38 3e38 3e38\n")
    df = b.to_pandas()
    assert df.isna().all(axis=None)
    assert all(df[c].dtype == np.float64 for c in df.columns)


# -- date and time ------------------------------------------------------------------------------


def test_geopoints_parser_time_values(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#DATA\n"
        "1 2 0 20200101 12 1\n"
        "1 2 0 20200101 0600 2\n"
        "1 2 0 20200101 600 3\n"
        "1 2 0 20200101 1200 4\n"
        "1 2 0 20200101 0 5\n"
        "1 2 0 20200101 1530.9 6\n"
        "1 2 0 20200101.7 2359 7\n",
    )
    df = b.to_pandas()
    assert df["date"].dtype == np.dtype("datetime64[ns]")
    assert df["date"].tolist() == [
        pd.Timestamp("2020-01-01T00:12"),
        pd.Timestamp("2020-01-01T06:00"),
        pd.Timestamp("2020-01-01T06:00"),
        pd.Timestamp("2020-01-01T12:00"),
        pd.Timestamp("2020-01-01T00:00"),
        pd.Timestamp("2020-01-01T15:30"),
        pd.Timestamp("2020-01-01T23:59"),
    ]


def test_geopoints_parser_date_zero_is_nat(tmp_path):
    b = _parse_block(tmp_path, "#GEO\n#DATA\n1 2 0 0 0 5\n1 2 0 20200101 1200 6\n")
    df = b.to_pandas()
    assert df["date"].dtype == np.dtype("datetime64[ns]")
    assert pd.isna(df["date"].iloc[0])
    assert df["date"].iloc[1] == _ts("2020-01-01T12:00")


def test_geopoints_parser_ncols_date_without_time(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude date t2\n#DATA\n10 20 20120218 1\n11 21 20120219 3\n",
    )
    assert b.columns == ["stnid", "latitude", "longitude", "date", "t2"]
    df = b.to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "date", "t2"]
    assert df["date"].tolist() == [pd.Timestamp("2012-02-18"), pd.Timestamp("2012-02-19")]


def test_geopoints_parser_ncols_time_without_date(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude time t2\n#DATA\n10 20 12 1\n11 21 0600 3\n",
    )
    df = b.to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "time", "t2"]
    assert "date" not in df.columns
    assert df["time"].dtype == np.int64
    assert df["time"].tolist() == [12, 600]


def test_geopoints_parser_ncols_date_zero_is_nat(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude date time\n#DATA\n10 20 0 1200 5\n11 21 20120219 600 6\n",
    )
    df = b.to_pandas()
    assert pd.isna(df["date"].iloc[0])
    assert df["date"].iloc[1] == _ts("2012-02-19T06:00")
    assert list(df.columns) == ["stnid", "latitude", "longitude", "date", "_v1"]


# -- NCOLS --------------------------------------------------------------------------------------


def test_geopoints_parser_ncols_without_stnid_adds_first_column(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude t2 value2\n#DATA\n10 20 1 2\n11 21 3 4\n",
    )
    assert b.columns == ["stnid", "latitude", "longitude", "t2", "value2"]
    df = b.to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "t2", "value2"]
    assert df["stnid"].dtype == object
    assert df["stnid"].tolist() == [None, None]
    assert df["t2"].tolist() == [1.0, 3.0]
    assert df["value2"].tolist() == [2.0, 4.0]


def test_geopoints_parser_ncols_unnamed_values(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nstnid latitude longitude time date level t2\n#DATA\n"
        "abc 1 2 0600 20200101 10 273.5 1 2\n",
    )
    assert b.columns == ["stnid", "latitude", "longitude", "time", "date", "level", "t2", "_v1", "_v2"]
    df = b.to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "date", "level", "t2", "_v1", "_v2"]
    assert (df["t2"].iloc[0], df["_v1"].iloc[0], df["_v2"].iloc[0]) == (273.5, 1.0, 2.0)


def test_geopoints_parser_ncols_elevation_and_order(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nelevation longitude stnid latitude value\n#DATA\n350 2 abc 1 9.5\n",
    )
    df = b.to_pandas()
    assert list(df.columns) == ["elevation", "longitude", "stnid", "latitude", "value"]
    assert df["elevation"].iloc[0] == 350.0
    assert df["stnid"].iloc[0] == "abc"
    assert df["value"].iloc[0] == 9.5


def test_geopoints_parser_ncols_format_prefix(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT   NCOLUMNS\n#COLUMNS\nlatitude longitude t2\n#DATA\n10 20 1\n",
    )
    assert b.format == "NCOLS"


def test_geopoints_parser_ncols_default_columns(tmp_path):
    # no #COLUMNS: the default coordinate columns are used
    b = _parse_block(tmp_path, "#GEO\n#FORMAT NCOLS\n#DATA\nabc 1 2 10 20200101 1200 350 5.5\n")
    assert b.columns == ["stnid", "latitude", "longitude", "level", "date", "time", "elevation", "_v1"]
    df = b.to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "level", "date", "elevation", "_v1"]
    assert df["stnid"].iloc[0] == "abc"
    assert df["elevation"].iloc[0] == 350.0


def test_geopoints_parser_stnid_decoding(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nstnid latitude longitude t2\n#DATA\n"
        "? 1 2 1\n"
        "new\\32\\york 1 2 2\n"
        "a\\9\\b 1 2 3\n"
        "\\32\\\\9\\? 1 2 4\n"
        "NA 1 2 5\n"
        "007 1 2 6\n"
        "nan 1 2 7\n"
        "null 1 2 8\n",
    )
    df = b.to_pandas()
    assert df["stnid"].dtype == object
    assert df["stnid"].tolist() == [None, "new york", "a\tb", " \t?", "NA", "007", "nan", "null"]
    assert df["t2"].tolist() == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]


def test_geopoints_parser_ncols_no_data(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude time date t2\n#DATA\n",
    )
    assert b.columns == ["stnid", "latitude", "longitude", "time", "date", "t2"]
    df = b.to_pandas()
    assert len(df) == 0
    assert list(df.columns) == ["stnid", "latitude", "longitude", "date", "t2"]
    assert df["date"].dtype == np.dtype("datetime64[ns]")
    assert df["t2"].dtype == np.float64
    assert df["stnid"].dtype == object


# -- text values (D2) ---------------------------------------------------------------------------


def test_geopoints_parser_text_values(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#DATA\n"
        "1 2 0 20200101 1200 5.5\n"
        "1 2 0 20200101 1200 hello\n"
        "1 2 0 20200101 1200 3e38\n"
        "1 2 0 20200101 1200 -7\n"
        "1 2 0 20200101 1200 1.5e3x\n",
    )
    df = b.to_pandas()
    assert df["value"].dtype == object
    v = df["value"].tolist()
    assert v[0] == 5.5 and isinstance(v[0], float)
    assert v[1] == "hello"
    assert isinstance(v[2], float) and np.isnan(v[2])
    assert v[3] == -7.0 and isinstance(v[3], float)
    assert v[4] == "1.5e3x"
    # the other columns are not affected
    assert df["latitude"].dtype == np.float64


def test_geopoints_parser_text_values_xyv(tmp_path):
    b = _parse_block(tmp_path, "#GEO\n#FORMAT XYV\n#DATA\n10 20 abc\n11 21 4.5\n")
    df = b.to_pandas()
    assert df["value"].dtype == object
    assert df["value"].tolist() == ["abc", 4.5]


def test_geopoints_parser_numeric_values_stay_float(tmp_path):
    b = _parse_block(tmp_path, "#GEO\n#DATA\n1 2 0 20200101 1200 5\n1 2 0 20200101 1200 6\n")
    assert b.to_pandas()["value"].dtype == np.float64


def _header(fmt):
    # TRADITIONAL is the default, there is no keyword for it
    return "#GEO\n#FORMAT XYV\n" if fmt == "XYV" else "#GEO\n"


_NOT_NUMBERS = ["inf", "-inf", "+inf", "Infinity", "-Infinity", "INF", "nan", "NaN", "-nan", "1e", "e5", ".", "1.5.3"]


@pytest.mark.parametrize("fmt", ["TRADITIONAL", "XYV"])
@pytest.mark.parametrize("token", _NOT_NUMBERS)
def test_geopoints_parser_non_numbers_alone_stay_text(tmp_path, fmt, token):
    # Metview's grammar does not know inf or nan: a column of them is text
    prefix = "1 2 0 20200101 1200" if fmt == "TRADITIONAL" else "1 2"
    b = _parse_block(tmp_path, f"{_header(fmt)}#DATA\n{prefix} {token}\n{prefix} {token}\n")
    v = b.to_pandas()["value"]
    assert v.dtype == object
    assert v.tolist() == [token, token]


@pytest.mark.parametrize("fmt", ["TRADITIONAL", "XYV"])
def test_geopoints_parser_non_numbers_mixed_with_numbers_and_text(tmp_path, fmt):
    tokens = ["inf", "5.5", "-inf", "Infinity", "nan", "NaN", "hello", "3e38", "-2", "3.0E+38", "3e+38"]
    prefix = "1 2 0 20200101 1200" if fmt == "TRADITIONAL" else "1 2"
    rows = "".join(f"{prefix} {t}\n" for t in tokens)
    b = _parse_block(tmp_path, f"{_header(fmt)}#DATA\n{rows}")
    v = b.to_pandas()["value"]
    assert v.dtype == object
    out = v.tolist()
    for i in (0, 2, 3, 4, 5, 6):
        assert isinstance(out[i], str) and out[i] == tokens[i]
    assert out[1] == 5.5 and isinstance(out[1], float)
    assert out[8] == -2.0 and isinstance(out[8], float)
    for i in (7, 9, 10):
        assert isinstance(out[i], float) and np.isnan(out[i])


@pytest.mark.parametrize("fmt", ["TRADITIONAL", "XYV"])
def test_geopoints_parser_non_numbers_with_numbers_only(tmp_path, fmt):
    prefix = "1 2 0 20200101 1200" if fmt == "TRADITIONAL" else "1 2"
    b = _parse_block(tmp_path, f"{_header(fmt)}#DATA\n{prefix} 1.5\n{prefix} inf\n{prefix} 2\n")
    assert b.to_pandas()["value"].tolist() == [1.5, "inf", 2.0]


@pytest.mark.parametrize("fmt", ["TRADITIONAL", "XYV"])
def test_geopoints_parser_number_spellings(tmp_path, fmt):
    # optional sign, digits with optional decimal point (at least one digit), optional exponent
    tokens = ["5", "+5", "-5", "5.", ".5", "-.5", "5.25", "1e3", "1E3", "1e+3", "1.5e-3", "5.e2", ".5E1"]
    expected = [5.0, 5.0, -5.0, 5.0, 0.5, -0.5, 5.25, 1000.0, 1000.0, 1000.0, 0.0015, 500.0, 5.0]
    prefix = "1 2 0 20200101 1200" if fmt == "TRADITIONAL" else "1 2"
    rows = "".join(f"{prefix} {t}\n" for t in tokens)
    b = _parse_block(tmp_path, f"{_header(fmt)}#DATA\n{rows}")
    v = b.to_pandas()["value"]
    assert v.dtype == np.float64
    assert v.tolist() == expected


@pytest.mark.parametrize("fmt", ["TRADITIONAL", "XYV"])
def test_geopoints_parser_numeric_only_column_is_float64(tmp_path, fmt):
    prefix = "1 2 0 20200101 1200" if fmt == "TRADITIONAL" else "1 2"
    b = _parse_block(
        tmp_path,
        f"{_header(fmt)}#DATA\n{prefix} 5\n{prefix} 3e38\n{prefix} 3.0E+38\n{prefix} 3e+38\n{prefix} 1.1\n",
    )
    v = b.to_pandas()["value"]
    assert v.dtype == np.float64
    assert v.iloc[0] == 5.0 and v.iloc[4] == 1.1
    assert v.iloc[1:4].isna().all()


# -- format keyword and line rules -------------------------------------------------------------


def test_geopoints_parser_unknown_format_warns(tmp_path):
    path = _write(tmp_path, "#GEO\n#FORMAT FOOBAR\n#DATA\n1 2 0 20200101 1200 5\n")
    with pytest.warns(UserWarning, match="FOOBAR"):
        f = parse_geopoints(path)
    b = f.blocks[0]
    assert b.format == "TRADITIONAL"
    assert list(b.to_pandas().columns) == ["latitude", "longitude", "level", "date", "value"]


def test_geopoints_parser_llv_alias(tmp_path):
    b = _parse_block(tmp_path, "#GEO\n#FORMAT LLV\n#DATA\n10 20 5\n")
    assert b.format == "XYV"
    assert list(b.to_pandas().columns) == ["longitude", "latitude", "value"]


def test_geopoints_parser_extra_trailing_tokens_ignored(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#DATA\n1 2 0 20200101 1200 5 99 foo\n3 4 0 20200101 1200 6\n5 6 0 20200101 1200 7 8\n",
    )
    df = b.to_pandas()
    assert len(df) == 3
    assert df["value"].tolist() == [5.0, 6.0, 7.0]
    assert df["latitude"].tolist() == [1.0, 3.0, 5.0]

    b = _parse_block(tmp_path, "#GEO\n#FORMAT XY_VECTOR\n#DATA\n1 2 0 20200101 1200 5 6 7\n")
    assert b.to_pandas()["y-comp"].tolist() == [6.0]


def test_geopoints_parser_skipped_data_lines(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#DATA\n"
        "# a comment line in the data section\n"
        "1 2 0 20200101 1200 5\n"
        "\n"
        "1 2\n"
        "abcd\n"
        "   \n"
        "#1 2 0 20200101 1200 99\n"
        "3 4 0 20200101 1200 6\n",
    )
    df = b.to_pandas()
    assert df["value"].tolist() == [5.0, 6.0]


def test_geopoints_parser_whitespace_and_line_endings(tmp_path):
    path = tmp_path / "crlf.gpt"
    path.write_bytes(b"#GEO\r\n#DATA\r\n  1\t2   0 20200101\t1200 5\r\n3 4 0 20200101 1200 6   \r\n")
    df = parse_geopoints(str(path)).blocks[0].to_pandas()
    assert df["latitude"].tolist() == [1.0, 3.0]
    assert df["value"].tolist() == [5.0, 6.0]


def test_geopoints_parser_header_lines_ignored(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\nPARAMETER = 12004\nlat long level date time value\n# comment\n\n#DATA\n1 2 0 20200101 1200 5\n",
    )
    assert b.metadata == {}
    assert len(b.to_pandas()) == 1


def test_geopoints_parser_metadata_rules(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\n#METADATA\n"
        "param = temperature\n"
        "count=3\n"
        "x=1e3\n"
        "neg=-4\n"
        "empty=\n"
        "a=b=c\n"
        "no equals sign\n"
        "# a comment\n"
        "=\n"
        "nanvalue=nan\n"
        "#DB_INFO\n"
        "DB_QUERY_BEGIN select a from b where x=1\n"
        "#DATA\n1 2 0 20200101 1200 5\n",
    )
    assert b.metadata == {
        "param": "temperature",
        "count": 3,
        "x": 1000.0,
        "neg": -4,
        "nanvalue": "nan",
    }
    assert isinstance(b.metadata["count"], int)
    assert isinstance(b.metadata["x"], float)


def test_geopoints_parser_db_info_skipped(tmp_path):
    b = _parse_block(
        tmp_path,
        "#GEO\nlat long level date time value\n#DB_INFO\nDB_SYSTEM: ODB\n"
        "DB_COLUMN: lldegrees(lat@hdr);lldegrees(lon@hdr); ; ; ;obsvalue@body\n"
        "DB_QUERY_BEGIN select a from b where varno=1\nDB_QUERY_END\n#DATA\n36.150 -5.350 0.000 0 0000 295.10000000\n",
    )
    assert b.metadata == {}
    df = b.to_pandas()
    assert df["value"].tolist() == [295.1]
    assert pd.isna(df["date"].iloc[0])


def test_geopoints_parser_no_data_section(tmp_path):
    expected = {
        "": ["latitude", "longitude", "level", "date", "value"],
        "#FORMAT XYV\n": ["longitude", "latitude", "value"],
        "#FORMAT XY_VECTOR\n": ["latitude", "longitude", "level", "date", "x-comp", "y-comp"],
        "#FORMAT POLAR_VECTOR\n": ["latitude", "longitude", "level", "date", "magnitude", "angle"],
    }
    for header, columns in expected.items():
        b = _parse_block(tmp_path, f"#GEO\n{header}1 2 0 20200101 1200 5\n")
        df = b.to_pandas()
        assert len(df) == 0
        assert list(df.columns) == columns
        assert df["latitude"].dtype == np.float64
        if "date" in columns:
            assert df["date"].dtype == np.dtype("datetime64[ns]")

    b = _parse_block(tmp_path, "#GEO\n#FORMAT NCOLS\n#COLUMNS\nstnid latitude longitude t2\n1 2 0 20200101 1200 5\n")
    df = b.to_pandas()
    assert len(df) == 0
    assert list(df.columns) == ["stnid", "latitude", "longitude", "t2"]

    # #DATA but no rows
    b = _parse_block(tmp_path, "#GEO\n#DATA\n")
    assert len(b.to_pandas()) == 0


def test_geopoints_parser_set_block_without_data(tmp_path):
    f = parse_geopoints(
        _write(
            tmp_path,
            "#GEOPOINTSET\n#GEO\n#METADATA\nparam=a\n#GEO\n#DATA\n1 2 0 20200101 1200 5\n",
        )
    )
    assert len(f.blocks) == 2
    assert f.blocks[0].metadata == {"param": "a"}
    assert len(f.blocks[0].to_pandas()) == 0
    assert len(f.blocks[1].to_pandas()) == 1


# -- errors -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "header,row",
    [
        ("", "1 2 0 20200101 1200"),
        ("#FORMAT XYV\n", "1.5 2.5"),
        ("#FORMAT XY_VECTOR\n", "1 2 0 20200101 1200 5"),
        ("#FORMAT POLAR_VECTOR\n", "1 2 0 20200101 1200 5"),
    ],
)
def test_geopoints_parser_error_too_few_tokens(tmp_path, header, row):
    path = _write(tmp_path, f"#GEO\n{header}#DATA\n{row}\n", name="short.gpt")
    with pytest.raises(ValueError, match="short.gpt"):
        parse_geopoints(path)


def test_geopoints_parser_error_too_few_tokens_line_number(tmp_path):
    path = _write(
        tmp_path,
        "#GEO\n#DATA\n1 2 0 20200101 1200 5\n# comment\n1 2 0 20200101 1200\n",
        name="short.gpt",
    )
    with pytest.raises(ValueError, match=r"short\.gpt, line 5"):
        parse_geopoints(path)


def test_geopoints_parser_error_not_a_number(tmp_path):
    path = _write(tmp_path, "#GEO\n#DATA\n1 abc 0 20200101 1200 5\n", name="bad.gpt")
    with pytest.raises(ValueError, match="bad.gpt"):
        parse_geopoints(path)


def test_geopoints_parser_error_ncols_different_counts(tmp_path):
    path = _write(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude t2\n#DATA\n1 2 3\n4 5 6 7\n",
        name="ncols_bad.gpt",
    )
    with pytest.raises(ValueError, match=r"ncols_bad\.gpt, line 7"):
        parse_geopoints(path)

    path = _write(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude t2\n#DATA\n1 2 3\n4.5 5\n",
        name="ncols_bad.gpt",
    )
    with pytest.raises(ValueError, match="ncols_bad.gpt"):
        parse_geopoints(path)


def test_geopoints_parser_error_ncols_coordinate_after_value(tmp_path):
    path = _write(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude t2 longitude\n#DATA\n1 2 3\n",
        name="ncols_order.gpt",
    )
    with pytest.raises(ValueError, match="ncols_order.gpt"):
        parse_geopoints(path)


@pytest.mark.parametrize("names", ["longitude t2", "latitude t2", "t2 value", "lat long t2"])
def test_geopoints_parser_error_ncols_missing_lat_lon(tmp_path, names):
    path = _write(
        tmp_path,
        f"#GEO\n#FORMAT NCOLS\n#COLUMNS\n{names}\n#DATA\n1 2 3\n",
        name="ncols_nolatlon.gpt",
    )
    with pytest.raises(ValueError, match="ncols_nolatlon.gpt"):
        parse_geopoints(path)


def test_geopoints_parser_error_ncols_more_names_than_values(tmp_path):
    path = _write(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude t2 rh\n#DATA\n1 2 3\n",
        name="ncols_names.gpt",
    )
    with pytest.raises(ValueError, match="ncols_names.gpt"):
        parse_geopoints(path)


@pytest.mark.parametrize(
    "names,row",
    [
        ("latitude longitude _v1", "10 20 1 2"),
        ("latitude longitude _v2", "10 20 1 2 3"),
        ("latitude longitude t2 _v2", "10 20 1 2 3 4"),
    ],
)
def test_geopoints_parser_error_ncols_generated_name_collision(tmp_path, names, row):
    path = _write(
        tmp_path,
        f"#GEO\n#FORMAT NCOLS\n#COLUMNS\n{names}\n#DATA\n{row}\n",
        name="ncols_collision.gpt",
    )
    with pytest.raises(ValueError, match="ncols_collision.gpt"):
        parse_geopoints(path)


def test_geopoints_parser_ncols_generated_name_no_collision(tmp_path):
    # _v2 is not generated when there is only one unnamed value column
    b = _parse_block(
        tmp_path,
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude _v2\n#DATA\n10 20 1\n",
    )
    df = b.to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "_v2"]
    assert df["_v2"].tolist() == [1.0]


def test_geopoints_parser_error_in_second_set_block(tmp_path):
    path = _write(
        tmp_path,
        "#GEOPOINTSET\n#GEO\n#DATA\n1 2 0 20200101 1200 5\n#GEO\n#DATA\n1 2 0 20200101\n",
        name="set_bad.gpts",
    )
    with pytest.raises(ValueError, match=r"set_bad\.gpts, line 7"):
        parse_geopoints(path)


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
