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
import shutil
import warnings

import numpy as np
import pandas as pd
import pytest

from earthkit.data import from_source
from earthkit.data.data.csv import CSVData
from earthkit.data.data.geopoints import GeopointsData
from earthkit.data.data.text import TextData
from earthkit.data.readers.geopoints.reader import GeopointsReader
from earthkit.data.utils.testing import earthkit_test_data_file

GEOPOINTS_FILES = sorted(os.listdir(earthkit_test_data_file("geopoints")))


def _data_file(name):
    return earthkit_test_data_file("geopoints", name)


def _write(tmp_path, text, name="test.gpt"):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def _ts(s):
    return np.datetime64(s, "ns")


# -- detection --------------------------------------------------------------------------------


def test_geopoints_test_files_found():
    assert len(GEOPOINTS_FILES) == 9
    assert "geopointset.gpts" in GEOPOINTS_FILES


@pytest.mark.parametrize("name", GEOPOINTS_FILES)
def test_geopoints_reader_detection(name):
    d = from_source("file", _data_file(name))
    assert isinstance(d, GeopointsData)
    assert d._TYPE_NAME == "Geopoints"
    assert isinstance(d._reader, GeopointsReader)


@pytest.mark.parametrize("name", GEOPOINTS_FILES)
@pytest.mark.parametrize("new_name", ["renamed.txt", "no_extension"])
def test_geopoints_reader_detection_other_name(tmp_path, name, new_name):
    path = str(tmp_path / new_name)
    shutil.copy(_data_file(name), path)

    d = from_source("file", path)
    assert isinstance(d, GeopointsData)
    assert isinstance(d._reader, GeopointsReader)


def test_geopoints_reader_other_readers_not_affected():
    d = from_source("file", earthkit_test_data_file("test.csv"))
    assert isinstance(d, CSVData)

    d = from_source("file", earthkit_test_data_file("test.txt"))
    assert isinstance(d, TextData)


def test_geopoints_reader_invalid_kwargs():
    with pytest.warns(UserWarning, match="foo"):
        d = from_source("file", _data_file("traditional.gpt"), foo=1)
    assert isinstance(d, GeopointsData)


def test_geopoints_reader_available_types():
    d = from_source("file", _data_file("traditional.gpt"))
    assert d.available_types == ["pandas", "xarray", "featurelist"]


def test_geopoints_reader_parse_error(tmp_path):
    path = _write(tmp_path, "#GEO\n#DATA\n1 2 3\n")
    d = from_source("file", path)
    with pytest.raises(ValueError, match="test.gpt"):
        d.to_pandas()


def test_geopoints_reader_parsed_once():
    d = from_source("file", _data_file("traditional.gpt"))
    r = d._reader
    assert r._parsed is None
    d.to_pandas()
    parsed = r._parsed
    assert parsed is not None
    d.to_xarray()
    d.describe()
    repr(d)
    assert r._parsed is parsed


# -- to_pandas --------------------------------------------------------------------------------


def test_geopoints_to_pandas_traditional():
    df = from_source("file", _data_file("traditional.gpt")).to_pandas()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["latitude", "longitude", "level", "date", "value"]
    assert len(df) == 8
    r = df.iloc[0]
    assert r["latitude"] == 36.15
    assert r["longitude"] == -5.35
    assert r["level"] == 0.0
    assert r["date"] == _ts("2010-08-10T12:00")
    assert r["value"] == 300.9


def test_geopoints_to_pandas_ncols_stnid():
    df = from_source("file", _data_file("ncols_stnid.gpt")).to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "level", "date", "_v1", "_v2", "_v3"]
    assert len(df) == 4
    r = df.iloc[0]
    assert r["stnid"] == "heathrow"
    assert r["latitude"] == 32.55
    assert r["longitude"] == 35.85
    assert r["level"] == 10.0
    assert r["date"] == _ts("2012-02-18T06:00")
    assert (r["_v1"], r["_v2"], r["_v3"]) == (273.9, 29.0, 7.0)


def test_geopoints_to_pandas_ncols_without_stnid():
    df = from_source("file", _data_file("ncols.gpt")).to_pandas()
    assert list(df.columns) == ["stnid", "latitude", "longitude", "date", "t2", "o3", "td", "rh"]
    assert len(df) == 4
    r = df.iloc[0]
    assert r["stnid"] is None
    assert r["t2"] == 273.9


@pytest.mark.parametrize(
    "name,columns,first",
    [
        ("xyv.gpt", ["longitude", "latitude", "value"], (-5.35, 36.15, 300.9)),
        (
            "xy_vector.gpt",
            ["latitude", "longitude", "level", "date", "x-comp", "y-comp"],
            (80.0, 0.0, 0.0, _ts("2003-06-17T12:00"), -4.9001, -8.3126),
        ),
        (
            "polar_vector.gpt",
            ["latitude", "longitude", "level", "date", "magnitude", "angle"],
            (50.97, 6.05, 0.0, _ts("2003-06-14T12:00"), 4.0, 90.0),
        ),
    ],
)
def test_geopoints_to_pandas_formats(name, columns, first):
    df = from_source("file", _data_file(name)).to_pandas()
    assert list(df.columns) == columns
    assert tuple(df.iloc[0]) == first


def test_geopoints_to_pandas_missing_latlon():
    df = from_source("file", _data_file("missing_latlon.gpt")).to_pandas()
    assert len(df) == 7
    assert df["latitude"].isna().any()
    assert df["longitude"].isna().any()


def test_geopoints_to_pandas_set():
    df = from_source("file", _data_file("geopointset.gpts")).to_pandas()
    assert list(df.columns) == ["latitude", "longitude", "level", "date", "value"]
    assert len(df) == 4 + 1 + 3
    assert list(df.index) == list(range(8))
    r = df.iloc[0]
    assert r["latitude"] == 69.6523
    assert r["longitude"] == 18.9057
    assert r["date"] == _ts("2013-05-12T00:00")
    assert r["value"] == 100869.8625
    # first row of block 2 and 3
    assert df.iloc[4]["latitude"] == 60.82
    assert df.iloc[4]["date"] == _ts("2013-05-12T06:00")
    assert df.iloc[5]["latitude"] == 55.01
    assert df.iloc[5]["date"] == _ts("2013-05-13T00:00")


def test_geopoints_to_pandas_returns_copy():
    d = from_source("file", _data_file("traditional.gpt"))
    df = d.to_pandas()
    df.loc[0, "value"] = -1.0
    df["extra"] = 1
    df2 = d.to_pandas()
    assert df2.iloc[0]["value"] == 300.9
    assert "extra" not in df2.columns


# -- to_xarray --------------------------------------------------------------------------------


def test_geopoints_to_xarray():
    import xarray as xr

    ds = from_source("file", _data_file("traditional.gpt")).to_xarray()
    assert isinstance(ds, xr.Dataset)
    assert set(ds.data_vars) == {"latitude", "longitude", "level", "date", "value"}
    assert ds["value"].shape == (8,)
    assert float(ds["value"][0]) == 300.9


def test_geopoints_to_xarray_ncols():
    import xarray as xr

    ds = from_source("file", _data_file("ncols_stnid.gpt")).to_xarray()
    assert isinstance(ds, xr.Dataset)
    assert set(ds.data_vars) == {"stnid", "latitude", "longitude", "level", "date", "_v1", "_v2", "_v3"}
    assert ds["stnid"].values[0] == "heathrow"


def test_geopoints_to_xarray_set():
    import xarray as xr

    ds = from_source("file", _data_file("geopointset.gpts")).to_xarray()
    assert isinstance(ds, xr.Dataset)
    assert set(ds.data_vars) == {"latitude", "longitude", "level", "date", "value"}
    assert ds["value"].shape == (8,)


def test_geopoints_to_xarray_kwargs():
    d = from_source("file", _data_file("xyv.gpt"))
    ds = d.to_xarray()
    assert set(ds.data_vars) == {"longitude", "latitude", "value"}
    assert "index" in ds.dims
    # the kwargs go to pandas.DataFrame.to_xarray, which does not take any
    with pytest.raises(TypeError):
        d.to_xarray(foo=1)


# -- removed interface ------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["metadata.gpt", "geopointset.gpts"])
def test_geopoints_no_set_interface(name):
    # the geopointset interface and metadata() are deliberately not exposed
    d = from_source("file", _data_file(name))
    assert not hasattr(GeopointsData, "__len__")
    assert not hasattr(GeopointsData, "__getitem__")
    assert not hasattr(GeopointsData, "metadata")
    assert not hasattr(d, "metadata")
    with pytest.raises(TypeError):
        len(d)
    with pytest.raises(TypeError):
        d[0]


# -- describe and repr ------------------------------------------------------------------------


def test_geopoints_describe():
    path = _data_file("ncols_stnid.gpt")
    d = from_source("file", path)
    desc = d.describe()
    assert desc.path == path
    assert desc.types == ["pandas", "xarray", "featurelist"]
    assert "Geopoints file" in desc.title
    assert "NCOLS" in desc.title
    s = str(desc)
    assert "NCOLS" in s
    assert path in s
    assert "pandas, xarray, featurelist" in s


def test_geopoints_describe_set():
    d = from_source("file", _data_file("geopointset.gpts"))
    desc = d.describe()
    assert "Geopointset" in desc.title
    assert "3 blocks" in desc.title
    assert "TRADITIONAL" in desc.title


def test_geopoints_repr():
    path = _data_file("traditional.gpt")
    d = from_source("file", path)
    assert repr(d) == f"GeopointsData(path={path}, blocks=1, format=TRADITIONAL)"

    path = _data_file("geopointset.gpts")
    d = from_source("file", path)
    assert repr(d) == f"GeopointsData(path={path}, blocks=3, format=TRADITIONAL)"


def test_geopoints_repr_html():
    d = from_source("file", _data_file("geopointset.gpts"))
    html = d._repr_html_()
    assert isinstance(html, str)
    assert "Geopointset" in html
    assert "geopointset.gpts" in html


# -- inline files -----------------------------------------------------------------------------

MIXED_SET = """#GEOPOINTSET
#GEO
#DATA
10.0 20.0 0 20130512 0 1.5
11.0 21.0 0 20130512 0 2.5
#GEO
#FORMAT NCOLS
#COLUMNS
latitude longitude date t2
#METADATA
param=temperature
#DATA
12.0 22.0 20130513 280.5
"""


def test_geopoints_set_different_columns(tmp_path):
    d = from_source("file", _write(tmp_path, MIXED_SET, "mixed.gpts"))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        df = d.to_pandas()

    assert list(df.columns) == ["latitude", "longitude", "level", "date", "value", "stnid", "t2"]
    assert len(df) == 3

    # missing columns are NaN
    assert df["value"].iloc[:2].tolist() == [1.5, 2.5]
    assert df["level"].iloc[:2].tolist() == [0.0, 0.0]
    assert df["t2"].iloc[:2].isna().all()
    assert np.isnan(df["value"].iloc[2])
    assert np.isnan(df["level"].iloc[2])
    assert df["t2"].iloc[2] == 280.5
    assert df["stnid"].iloc[:2].isna().all()
    assert df["stnid"].iloc[2] is None or pd.isna(df["stnid"].iloc[2])
    assert df["latitude"].tolist() == [10.0, 11.0, 12.0]
    assert df["date"].iloc[2] == _ts("2013-05-13T00:00")

    ds = d.to_xarray()
    assert {"t2", "value", "stnid"} <= set(ds.data_vars)
    assert ds["latitude"].shape == (3,)


def test_geopoints_set_empty(tmp_path):
    d = from_source("file", _write(tmp_path, "#GEOPOINTSET\n", "empty.gpts"))
    assert isinstance(d, GeopointsData)
    assert isinstance(d._reader, GeopointsReader)
    df = d.to_pandas()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert len(df.columns) == 0
    assert len(d.to_xarray().data_vars) == 0
    assert repr(d) == f"GeopointsData(path={d.path}, blocks=0)"
    assert "0 blocks" in d.describe().title
    assert "Geopointset" in d.describe().title


def test_geopoints_set_single_block(tmp_path):
    text = "#GEOPOINTSET\n#GEO\n#METADATA\nparam=t\n#DATA\n1 2 0 20130512 0 3.0\n"
    d = from_source("file", _write(tmp_path, text, "one.gpts"))
    assert "1 block," in d.describe().title
    assert len(d.to_pandas()) == 1


def test_geopoints_set_block_without_data(tmp_path):
    # a block with no points gives an empty frame with the columns of the format
    text = "#GEOPOINTSET\n#GEO\n#DATA\n1 2 0 20130512 0 3.0\n#GEO\n#DATA\n"
    d = from_source("file", _write(tmp_path, text, "nodata.gpts"))
    assert "2 blocks" in d.describe().title
    df = d.to_pandas()
    assert len(df) == 1
    assert list(df.columns) == ["latitude", "longitude", "level", "date", "value"]


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
