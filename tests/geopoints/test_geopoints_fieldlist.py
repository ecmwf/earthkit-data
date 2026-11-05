#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import os
import warnings

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.data.geopoints import GeopointsData
from earthkit.data.indexing.simple import SimpleFieldList
from earthkit.data.readers.geopoints.fieldlist import (
    GeopointsGeography,
    make_fieldlist,
)
from earthkit.data.utils.testing import earthkit_test_data_file

GEOPOINTS_FILES = sorted(os.listdir(earthkit_test_data_file("geopoints")))

NCOLS_COORDINATES = ("stnid", "latitude", "longitude", "level", "elevation", "date", "time")


def _data_file(name):
    return earthkit_test_data_file("geopoints", name)


def _write(tmp_path, text, name="test.gpt"):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def _fieldlist(name, **kwargs):
    return from_source("file", _data_file(name)).to_fieldlist(**kwargs)


def _inline(tmp_path, metadata="", rows=None, header="#GEO\n"):
    """Write a traditional geopoints file with the #METADATA lines in ``metadata``."""
    if rows is None:
        rows = ["50 10 850 20200101 1200 1.5", "51 11 850 20200101 1200 2.5"]
    text = header
    if metadata:
        text += "#METADATA\n" + metadata.strip("\n") + "\n"
    text += "#DATA\n" + "\n".join(rows) + "\n"
    return _write(tmp_path, text)


def _first(path, **kwargs):
    fl = from_source("file", path).to_fieldlist(**kwargs)
    assert len(fl) >= 1
    return fl[0]


def _dt(*args):
    return datetime.datetime(*args)


# -- creation ---------------------------------------------------------------------------------


@pytest.mark.parametrize("name", GEOPOINTS_FILES)
def test_geopoints_fieldlist_all_files(name):
    ds = from_source("file", _data_file(name))
    fl = ds.to_fieldlist()
    assert isinstance(fl, SimpleFieldList)

    # one field per block and value column
    blocks = ds._reader.blocks
    expected = 0
    for b in blocks:
        if len(b) == 0:
            continue
        if b.format == "TRADITIONAL" or b.format == "XYV":
            expected += 1
        elif b.format in ("XY_VECTOR", "POLAR_VECTOR"):
            expected += 2
        else:
            expected += len([c for c in b._frame.columns if c not in NCOLS_COORDINATES])
    assert len(fl) == expected

    for f in fl:
        lat = f.geography.latitudes()
        assert lat.shape == f.geography.shape() == f.values.shape
        assert lat.ndim == 1


def test_geopoints_fieldlist_default_is_block_mode():
    ds = from_source("file", _data_file("geopointset.gpts"))
    a = ds.to_fieldlist()
    b = ds.to_fieldlist(mode="block")
    assert len(a) == len(b) == 3
    for x, y in zip(a, b):
        np.testing.assert_array_equal(x.values, y.values)


def test_geopoints_fieldlist_ncols():
    fl = _fieldlist("ncols.gpt")
    assert fl.get("parameter.variable") == ["t2", "o3", "td", "rh"]

    frame = from_source("file", _data_file("ncols.gpt")).to_pandas()
    for f, name in zip(fl, ["t2", "o3", "td", "rh"]):
        np.testing.assert_array_equal(f.values, frame[name].to_numpy())
        np.testing.assert_array_equal(f.geography.latitudes(), frame["latitude"].to_numpy())
        np.testing.assert_array_equal(f.geography.longitudes(), frame["longitude"].to_numpy())
        # first row: 2012-02-18 06:00
        assert f.get("time.valid_datetime") == _dt(2012, 2, 18, 6, 0)
        assert f.get("vertical.level") is None


def test_geopoints_fieldlist_ncols_stnid():
    fl = _fieldlist("ncols_stnid.gpt")
    # three unnamed value columns
    assert fl.get("parameter.variable") == ["_v1", "_v2", "_v3"]
    frame = from_source("file", _data_file("ncols_stnid.gpt")).to_pandas()
    for f, name in zip(fl, ["_v1", "_v2", "_v3"]):
        np.testing.assert_array_equal(f.values, frame[name].to_numpy())
        assert f.get("vertical.level") == 10
        assert isinstance(f.get("vertical.level"), int)


def test_geopoints_fieldlist_xy_vector():
    fl = _fieldlist("xy_vector.gpt")
    assert fl.get("parameter.variable") == ["x-comp", "y-comp"]
    frame = from_source("file", _data_file("xy_vector.gpt")).to_pandas()
    np.testing.assert_array_equal(fl[0].values, frame["x-comp"].to_numpy())
    np.testing.assert_array_equal(fl[1].values, frame["y-comp"].to_numpy())
    for f in fl:
        assert f.get("time.valid_datetime") == _dt(2003, 6, 17, 12, 0)
        assert f.get("vertical.level") == 0


def test_geopoints_fieldlist_polar_vector():
    fl = _fieldlist("polar_vector.gpt")
    assert fl.get("parameter.variable") == ["magnitude", "angle"]
    frame = from_source("file", _data_file("polar_vector.gpt")).to_pandas()
    np.testing.assert_array_equal(fl[0].values, frame["magnitude"].to_numpy())
    np.testing.assert_array_equal(fl[1].values, frame["angle"].to_numpy())


@pytest.mark.parametrize("name", ["traditional.gpt", "xyv.gpt"])
def test_geopoints_fieldlist_single_value(name):
    fl = _fieldlist(name)
    assert len(fl) == 1
    assert fl[0].get("parameter.variable") == "value"
    frame = from_source("file", _data_file(name)).to_pandas()
    np.testing.assert_array_equal(fl[0].values, frame["value"].to_numpy())
    assert fl[0].values.dtype == np.float64
    assert fl[0].values.ndim == 1


def test_geopoints_fieldlist_xyv_no_time_no_level():
    f = _fieldlist("xyv.gpt")[0]
    assert f.get("time.valid_datetime") is None
    assert f.get("time.base_datetime") is None
    assert f.get("vertical.level") is None
    frame = from_source("file", _data_file("xyv.gpt")).to_pandas()
    np.testing.assert_array_equal(f.geography.latitudes(), frame["latitude"].to_numpy())
    np.testing.assert_array_equal(f.geography.longitudes(), frame["longitude"].to_numpy())


def test_geopoints_fieldlist_geopointset():
    fl = _fieldlist("geopointset.gpts")
    assert len(fl) == 3
    ds = from_source("file", _data_file("geopointset.gpts"))
    blocks = ds._reader.blocks
    assert [len(b) for b in blocks] == [4, 1, 3]
    assert fl.get("parameter.variable") == ["value", "geopotential", "value"]
    assert [f.values.shape for f in fl] == [(4,), (1,), (3,)]
    for f, b in zip(fl, blocks):
        np.testing.assert_array_equal(f.values, b._frame["value"].to_numpy())
    assert fl.get("time.valid_datetime") == [_dt(2013, 5, 12, 0, 0), _dt(2013, 5, 12, 6, 0), _dt(2013, 5, 13, 0, 0)]
    assert fl.get("labels.param") == [None, "geopotential", None]


def test_geopoints_fieldlist_empty_geopointset(tmp_path):
    path = _write(tmp_path, "#GEOPOINTSET\n", "empty.gpts")
    fl = from_source("file", path).to_fieldlist()
    assert isinstance(fl, SimpleFieldList)
    assert len(fl) == 0


def test_geopoints_fieldlist_block_without_rows(tmp_path):
    path = _write(tmp_path, "#GEOPOINTSET\n#GEO\n#DATA\n#GEO\n#DATA\n50 10 0 20200101 1200 1\n#GEO\n#DATA\n")
    ds = from_source("file", path)
    assert [len(b) for b in ds._reader.blocks] == [0, 1, 0]
    fl = ds.to_fieldlist()
    assert len(fl) == 1
    assert fl[0].values.tolist() == [1.0]


def test_geopoints_fieldlist_ncols_block_without_rows(tmp_path):
    text = "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude date a b\n#DATA\n"
    fl = from_source("file", _write(tmp_path, text)).to_fieldlist()
    assert len(fl) == 0


# -- metadata, F4 and F5 ----------------------------------------------------------------------------


def test_geopoints_fieldlist_metadata_file():
    fl = _fieldlist("metadata.gpt")
    assert len(fl) == 1
    f = fl[0]
    assert f.get("parameter.variable") == "temperature"
    assert f.get("time.valid_datetime") == _dt(2013, 8, 4, 12, 0)
    assert f.get("time.base_datetime") == _dt(2013, 8, 4, 12, 0)
    assert f.get("time.step") == datetime.timedelta(0)
    assert f.get("vertical.level") == 0.2
    assert f.get("labels.param") == "temperature"
    # all the pairs are labels with the parsed types
    assert f.get("labels.date") == 20130804
    assert f.get("labels.time") == 1200
    assert f.get("labels.level") == 0.2


def test_geopoints_fieldlist_values_lat_lon_nan():
    ds = from_source("file", _data_file("missing_latlon.gpt"))
    frame = ds.to_pandas()
    f = ds.to_fieldlist()[0]

    assert np.isnan(frame["latitude"]).any() and np.isnan(frame["longitude"]).any()
    np.testing.assert_array_equal(f.values, frame["value"].to_numpy())
    np.testing.assert_array_equal(f.geography.latitudes(), frame["latitude"].to_numpy())
    np.testing.assert_array_equal(f.geography.longitudes(), frame["longitude"].to_numpy())
    assert np.isnan(f.geography.latitudes()).sum() == 2
    assert np.isnan(f.geography.longitudes()).sum() == 2
    # first row
    assert f.get("time.valid_datetime") == _dt(2013, 8, 4, 12, 0)
    assert f.get("vertical.level") == 0.2


def test_geopoints_fieldlist_missing_values_stay_nan():
    f = _fieldlist("traditional.gpt")[0]
    frame = from_source("file", _data_file("traditional.gpt")).to_pandas()
    assert np.isnan(f.values).sum() == 1
    np.testing.assert_array_equal(f.values, frame["value"].to_numpy())


def test_geopoints_fieldlist_values_are_copies():
    ds = from_source("file", _data_file("traditional.gpt"))
    f = ds.to_fieldlist()[0]
    before = ds.to_pandas()["value"].to_numpy().copy()
    f.values[0] = -1
    np.testing.assert_array_equal(ds.to_pandas()["value"].to_numpy(), before)


@pytest.mark.parametrize(
    "step,delta",
    [
        ("6", datetime.timedelta(hours=6)),
        ("1.5", datetime.timedelta(hours=1.5)),
        ("6h", datetime.timedelta(hours=6)),
        ("30m", datetime.timedelta(minutes=30)),
        ("0", datetime.timedelta(0)),
    ],
)
def test_geopoints_fieldlist_step(tmp_path, step, delta):
    f = _first(_inline(tmp_path, f"step={step}"))
    valid = _dt(2020, 1, 1, 12, 0)
    assert f.get("time.valid_datetime") == valid
    assert f.get("time.step") == delta
    assert f.get("time.base_datetime") == valid - delta
    assert f.get("labels.step") is not None


def test_geopoints_fieldlist_no_step_is_zero(tmp_path):
    f = _first(_inline(tmp_path, "param=t"))
    assert f.get("time.step") == datetime.timedelta(0)
    assert f.get("time.base_datetime") == f.get("time.valid_datetime") == _dt(2020, 1, 1, 12, 0)


@pytest.mark.parametrize("step", ["abc", "nan", "6x", "2020-01-01"])
def test_geopoints_fieldlist_bad_step(tmp_path, step):
    path = _inline(tmp_path, f"step={step}")
    with pytest.raises(ValueError, match="test.gpt") as e:
        from_source("file", path).to_fieldlist()
    assert "step" in str(e.value)


def test_geopoints_fieldlist_units_and_level_type(tmp_path):
    f = _first(_inline(tmp_path, "param=t\nunits=K\nlevtype=pl"))
    assert f.get("parameter.variable") == "t"
    assert f.get("parameter.units") == "K"
    assert f.get("vertical.level_type") == "pressure"
    assert f.get("vertical.level") == 850


@pytest.mark.parametrize(
    "key,value,expected",
    [
        ("levtype", "sfc", "surface"),
        ("levtype", "ml", "hybrid"),
        ("level_type", "pl", "pressure"),
        ("typeOfLevel", "isobaricInhPa", "isobaricInhPa"),
        ("levtype", "pressure", "pressure"),
    ],
)
def test_geopoints_fieldlist_level_type_keys(tmp_path, key, value, expected):
    f = _first(_inline(tmp_path, f"{key}={value}"))
    assert f.get("vertical.level_type") == expected


def test_geopoints_fieldlist_no_units_no_level_type(tmp_path):
    f = _first(_inline(tmp_path, "param=t"))
    # the default of the parameter component
    assert str(f.get("parameter.units")) == "dimensionless"
    assert f.get("vertical.level_type") == "unknown"


def test_geopoints_fieldlist_param_short_name(tmp_path):
    f = _first(_inline(tmp_path, "shortName=2t"))
    assert f.get("parameter.variable") == "2t"
    assert f.get("labels.shortName") == "2t"

    # param wins
    f = _first(_inline(tmp_path, "shortName=2t\nparam=temperature"))
    assert f.get("parameter.variable") == "temperature"


def test_geopoints_fieldlist_numeric_param(tmp_path):
    f = _first(_inline(tmp_path, "param=130"))
    assert f.get("parameter.variable") == "130"
    assert f.get("labels.param") == 130


def test_geopoints_fieldlist_param_ignored_for_several_columns(tmp_path):
    path = _write(
        tmp_path,
        "#GEO\n#FORMAT XY_VECTOR\n#METADATA\nparam=wind\n#DATA\n50 10 0 20200101 1200 1 2\n",
    )
    fl = from_source("file", path).to_fieldlist()
    assert fl.get("parameter.variable") == ["x-comp", "y-comp"]
    assert fl.get("labels.param") == ["wind", "wind"]


def test_geopoints_fieldlist_xyv_metadata_time_level(tmp_path):
    path = _write(
        tmp_path,
        "#GEO\n#FORMAT XYV\n#METADATA\nparam=t\ndate=20130804\ntime=0600\nlevel=500\n#DATA\n10 50 1\n11 51 2\n",
    )
    f = _first(path)
    assert f.get("time.valid_datetime") == _dt(2013, 8, 4, 6, 0)
    assert f.get("time.step") == datetime.timedelta(0)
    assert f.get("vertical.level") == 500
    assert isinstance(f.get("vertical.level"), int)


def test_geopoints_fieldlist_xyv_metadata_date_only_and_step(tmp_path):
    path = _write(
        tmp_path,
        "#GEO\n#FORMAT XYV\n#METADATA\ndate=20130804\nstep=12\nlevel=0.5\n#DATA\n10 50 1\n",
    )
    f = _first(path)
    assert f.get("time.valid_datetime") == _dt(2013, 8, 4, 0, 0)
    assert f.get("time.base_datetime") == _dt(2013, 8, 3, 12, 0)
    assert f.get("time.step") == datetime.timedelta(hours=12)
    assert f.get("vertical.level") == 0.5
    assert isinstance(f.get("vertical.level"), float)


def test_geopoints_fieldlist_xyv_without_metadata(tmp_path):
    path = _write(tmp_path, "#GEO\n#FORMAT XYV\n#METADATA\nparam=t\n#DATA\n10 50 1\n")
    f = _first(path)
    assert f.get("time.valid_datetime") is None
    assert f.get("time.base_datetime") is None
    assert f.get("time.step") is None
    assert f.get("vertical.level") is None


def test_geopoints_fieldlist_xyv_time_without_date(tmp_path):
    # a time alone is not enough
    path = _write(tmp_path, "#GEO\n#FORMAT XYV\n#METADATA\ntime=1200\n#DATA\n10 50 1\n")
    assert _first(path).get("time.valid_datetime") is None


@pytest.mark.parametrize("meta", ["date=abc", "date=20130804\ntime=xyz", "date=20131304", "date=20130804.5"])
def test_geopoints_fieldlist_bad_metadata_date(tmp_path, meta):
    path = _write(tmp_path, f"#GEO\n#FORMAT XYV\n#METADATA\n{meta}\n#DATA\n10 50 1\n")
    with pytest.raises(ValueError, match="test.gpt"):
        from_source("file", path).to_fieldlist()


def test_geopoints_fieldlist_bad_metadata_level(tmp_path):
    path = _write(tmp_path, "#GEO\n#FORMAT XYV\n#METADATA\nlevel=top\n#DATA\n10 50 1\n")
    with pytest.raises(ValueError, match="test.gpt"):
        from_source("file", path).to_fieldlist()


def test_geopoints_fieldlist_row_date_wins_over_metadata(tmp_path):
    f = _first(_inline(tmp_path, "date=19990101\ntime=0000\nlevel=1"))
    assert f.get("time.valid_datetime") == _dt(2020, 1, 1, 12, 0)
    assert f.get("vertical.level") == 850


def test_geopoints_fieldlist_first_row_only(tmp_path):
    rows = [
        "50 10 850 20200101 1200 1",
        "51 11 700 20200102 1800 2",
    ]
    f = _first(_inline(tmp_path, rows=rows))
    assert f.get("time.valid_datetime") == _dt(2020, 1, 1, 12, 0)
    assert f.get("vertical.level") == 850
    assert f.values.tolist() == [1.0, 2.0]


def test_geopoints_fieldlist_nat_date_and_nan_level(tmp_path):
    rows = ["50 10 3e+38 0 0 1", "51 11 700 20200102 1800 2"]
    f = _first(_inline(tmp_path, "level=5", rows=rows))
    assert f.get("time.valid_datetime") is None
    assert f.get("vertical.level") is None
    assert f.values.tolist() == [1.0, 2.0]


def test_geopoints_fieldlist_labels(tmp_path):
    f = _first(_inline(tmp_path, "param=t\nexpver=0001\nnumber=3\nfactor=1.5\nname=abc"))
    assert f.get("labels.param") == "t"
    assert f.get("labels.expver") == 1
    assert f.get("labels.number") == 3
    assert f.get("labels.factor") == 1.5
    assert f.get("labels.name") == "abc"
    assert type(f.get("labels.number")) is int


def test_geopoints_fieldlist_no_metadata_labels_empty(tmp_path):
    f = _first(_inline(tmp_path))
    assert f.get("labels.param") is None
    assert f.get("parameter.variable") == "value"


# -- value columns ----------------------------------------------------------------------------------


def test_geopoints_fieldlist_text_value_column_skipped(tmp_path):
    rows = ["50 10 0 20200101 1200 abc", "51 11 0 20200101 1200 2"]
    path = _inline(tmp_path, rows=rows)
    with pytest.warns(UserWarning, match="test.gpt") as w:
        fl = from_source("file", path).to_fieldlist()
    assert len(fl) == 0
    msgs = [str(x.message) for x in w]
    assert any("'value'" in m and "not numeric" in m for m in msgs)


def test_geopoints_fieldlist_text_value_column_skipped_in_set(tmp_path):
    text = "#GEOPOINTSET\n#GEO\n#DATA\n50 10 0 20200101 1200 abc\n#GEO\n#DATA\n50 10 0 20200101 1200 7\n"
    path = _write(tmp_path, text, "set.gpts")
    with pytest.warns(UserWarning, match="set.gpts"):
        fl = from_source("file", path).to_fieldlist()
    assert len(fl) == 1
    assert fl[0].values.tolist() == [7.0]


def test_geopoints_fieldlist_numeric_values_no_warning(tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fl = from_source("file", _inline(tmp_path)).to_fieldlist()
    assert len(fl) == 1


# -- geography --------------------------------------------------------------------------------------


def test_geopoints_fieldlist_geography_shape(tmp_path):
    f = _first(_inline(tmp_path))
    assert f.geography.shape() == (2,)
    assert f.shape == (2,)
    assert f.geography.grid_type() == "_unstructured"
    assert f.geography.latitudes().dtype == np.float64
    assert f.geography.latitudes().tolist() == [50.0, 51.0]
    assert f.geography.longitudes().tolist() == [10.0, 11.0]


def test_geopoints_fieldlist_geography_one_point(tmp_path):
    f = _first(_inline(tmp_path, rows=["50 10 850 20200101 1200 1.5"]))
    assert f.geography.shape() == (1,)
    assert f.shape == (1,)
    assert f.geography.latitudes().shape == (1,)
    assert f.values.shape == (1,)
    assert f.to_numpy().shape == (1,)


def test_geopoints_geography_class():
    g = GeopointsGeography([1.0], [2.0])
    assert g.shape() == (1,)
    g = GeopointsGeography([], [])
    assert g.shape() == (0,)
    assert g.unique_grid_id() == GeopointsGeography([], []).unique_grid_id()


def test_geopoints_fieldlist_grid_id(tmp_path):
    p1 = _inline(tmp_path, rows=["50 10 0 20200101 1200 1", "51 11 0 20200101 1200 2"])
    p2 = _write(tmp_path, "#GEO\n#DATA\n50 10 0 20200101 1200 1\n52 11 0 20200101 1200 2\n", "other.gpt")
    p3 = _write(tmp_path, "#GEO\n#DATA\n50 10 0 20200101 1200 9\n51 11 0 20200101 1200 8\n", "same.gpt")

    a = _first(p1).geography.unique_grid_id()
    b = _first(p2).geography.unique_grid_id()
    c = _first(p3).geography.unique_grid_id()

    # same number of points, different coordinates
    assert a != b
    # same points, other values
    assert a == c


def test_geopoints_fieldlist_grid_id_same_for_value_columns():
    fl = _fieldlist("ncols.gpt")
    ids = {f.geography.unique_grid_id() for f in fl}
    assert len(ids) == 1


def test_geopoints_fieldlist_grid_id_different_blocks():
    fl = _fieldlist("geopointset.gpts")
    ids = [f.geography.unique_grid_id() for f in fl]
    assert len(set(ids)) == 3


def test_geopoints_fieldlist_grid_id_nan_points():
    lat = [50.0, np.nan, 52.0]
    lon = [10.0, 11.0, np.nan]

    # independent objects built from separate arrays with the same coordinates, NaN included
    a = GeopointsGeography(list(lat), list(lon)).unique_grid_id()
    b = GeopointsGeography(np.array(lat), np.array(lon)).unique_grid_id()
    assert a == b

    # one coordinate changed
    c = GeopointsGeography([50.0, np.nan, 53.0], list(lon)).unique_grid_id()
    assert a != c


# -- FieldList operations ---------------------------------------------------------------------------


def test_geopoints_fieldlist_sel():
    fl = _fieldlist("geopointset.gpts")

    r = fl.sel({"labels.param": "geopotential"})
    assert len(r) == 1
    assert r[0].values.shape == (1,)

    r = fl.sel({"parameter.variable": "value"})
    assert len(r) == 2

    r = fl.sel({"parameter.variable": "geopotential", "labels.param": "geopotential"})
    assert len(r) == 1


def test_geopoints_fieldlist_sel_ncols():
    fl = _fieldlist("ncols.gpt")
    r = fl.sel({"parameter.variable": "o3"})
    assert len(r) == 1
    frame = from_source("file", _data_file("ncols.gpt")).to_pandas()
    np.testing.assert_array_equal(r[0].values, frame["o3"].to_numpy())


def test_geopoints_fieldlist_order_by():
    fl = _fieldlist("ncols.gpt")
    r = fl.order_by("parameter.variable")
    assert r.get("parameter.variable") == ["o3", "rh", "t2", "td"]

    r = fl.order_by({"parameter.variable": "descending"})
    assert r.get("parameter.variable") == ["td", "t2", "rh", "o3"]

    fl = _fieldlist("geopointset.gpts")
    r = fl.order_by("time.valid_datetime")
    assert r.get("time.valid_datetime") == sorted(fl.get("time.valid_datetime"))


def test_geopoints_fieldlist_ls():
    fl = _fieldlist("metadata.gpt")
    df = fl.ls()
    assert len(df) == 1
    assert df["parameter.variable"].tolist() == ["temperature"]
    assert df["geography.grid_type"].tolist() == ["_unstructured"]

    df = fl.ls(extra_keys=["labels.param"])
    assert df["labels.param"].tolist() == ["temperature"]


def test_geopoints_fieldlist_to_numpy():
    fl = _fieldlist("ncols.gpt")
    frame = from_source("file", _data_file("ncols.gpt")).to_pandas()
    for f, name in zip(fl, ["t2", "o3", "td", "rh"]):
        a = f.to_numpy()
        assert a.shape == (4,)
        np.testing.assert_array_equal(a, frame[name].to_numpy())

    # same number of points: the list can be stacked
    assert fl.to_numpy().shape == (4, 4)


def test_geopoints_fieldlist_to_xarray_single_block():
    # all the fields share one point set, so xarray conversion works
    ds = _fieldlist("ncols.gpt").to_xarray()
    frame = from_source("file", _data_file("ncols.gpt")).to_pandas()
    assert set(ds.data_vars) == {"t2", "o3", "td", "rh"}
    np.testing.assert_array_equal(ds["latitude"].values, frame["latitude"].to_numpy())
    np.testing.assert_array_equal(ds["longitude"].values, frame["longitude"].to_numpy())
    np.testing.assert_array_equal(ds["t2"].values, frame["t2"].to_numpy())


def test_geopoints_fieldlist_to_xarray_never_shares_coordinates(tmp_path):
    # Blocks with different points are different grids and must not be silently combined.
    fl = _fieldlist("geopointset.gpts")
    with pytest.raises(ValueError, match="same grid"):
        fl.to_xarray()

    # also when the number of points is the same: two blocks with 1 point each
    text = "#GEOPOINTSET\n#GEO\n#DATA\n50 10 0 20200101 1200 1\n#GEO\n#DATA\n60 20 0 20200101 1200 2\n"
    fl = from_source("file", _write(tmp_path, text, "same_n.gpts")).to_fieldlist()
    assert len(fl) == 2
    with pytest.raises(ValueError, match="same grid"):
        fl.to_xarray()


# -- several files ----------------------------------------------------------------------------------


def test_geopoints_fieldlist_two_files():
    names = ["ncols.gpt", "geopointset.gpts", "xy_vector.gpt"]
    ds = from_source("file", [_data_file(n) for n in names])
    assert ds._reader.is_multi
    fl = ds.to_fieldlist()

    expected = []
    for n in names:
        expected.extend(_fieldlist(n).get("parameter.variable"))
    assert fl.get("parameter.variable") == expected
    assert len(fl) == 4 + 3 + 2

    # the values are in order
    single = [f for n in names for f in _fieldlist(n)]
    for a, b in zip(fl, single):
        np.testing.assert_array_equal(a.values, b.values)


def test_geopoints_fieldlist_multi_message_names_file(tmp_path):
    p1 = _inline(tmp_path)
    p2 = _write(tmp_path, "#GEO\n#DATA\n50 10 0 20200101 1200 abc\n", "second.gpt")
    ds = from_source("file", [p1, p2])
    with pytest.warns(UserWarning, match="second.gpt"):
        fl = ds.to_fieldlist()
    assert len(fl) == 1


def test_geopoints_fieldlist_multi_error_names_file(tmp_path):
    p1 = _inline(tmp_path)
    p2 = _write(tmp_path, "#GEO\n#METADATA\nstep=abc\n#DATA\n50 10 0 20200101 1200 1\n", "second.gpt")
    ds = from_source("file", [p1, p2])
    with pytest.raises(ValueError, match="second.gpt"):
        ds.to_fieldlist()


# -- arguments and wiring ---------------------------------------------------------------------------


def test_geopoints_fieldlist_available_types():
    d = from_source("file", _data_file("traditional.gpt"))
    assert d.available_types == ["pandas", "xarray", "featurelist", "fieldlist"]
    assert GeopointsData._FIELDLIST == "fieldlist"


@pytest.mark.parametrize("mode", ["row", "blocks", "", None, 1])
def test_geopoints_fieldlist_bad_mode(mode):
    ds = from_source("file", _data_file("traditional.gpt"))
    with pytest.raises(ValueError, match="block") as e:
        ds.to_fieldlist(mode=mode)
    assert "group" in str(e.value)

    with pytest.raises(ValueError, match="block"):
        ds._reader.to_fieldlist(mode=mode)

    with pytest.raises(ValueError, match="block"):
        make_fieldlist([], mode=mode)


@pytest.mark.parametrize("group_by", [["stnid"], [], "level"])
def test_geopoints_fieldlist_group_by_with_block_mode(group_by):
    ds = from_source("file", _data_file("traditional.gpt"))
    with pytest.raises(ValueError, match="group_by"):
        ds.to_fieldlist(group_by=group_by)
    with pytest.raises(ValueError, match="group_by"):
        ds.to_fieldlist(mode="block", group_by=group_by)


def test_geopoints_fieldlist_bad_arguments_multi():
    ds = from_source("file", [_data_file("ncols.gpt"), _data_file("xyv.gpt")])
    with pytest.raises(ValueError, match="mode"):
        ds.to_fieldlist(mode="row")
    with pytest.raises(ValueError, match="group_by"):
        ds.to_fieldlist(group_by=["level"])


def test_geopoints_fieldlist_make_fieldlist_items():
    ds = from_source("file", _data_file("geopointset.gpts"))
    blocks = ds._reader.blocks
    fl = make_fieldlist([("a.gpt", b) for b in blocks])
    assert len(fl) == 3
    assert len(make_fieldlist([])) == 0


# -- group mode -------------------------------------------------------------------------------------

# 2 dates x 2 levels, the rows of a group are not next to each other
GROUP_ROWS = [
    "50 10 850 20200101 1200 1",
    "51 11 500 20200101 1200 2",
    "52 12 850 20200102 1200 3",
    "53 13 850 20200101 1200 4",
    "54 14 500 20200102 1200 5",
    "55 15 500 20200101 1200 6",
]

KEYS = ["parameter.variable", "time.valid_datetime", "time.base_datetime", "time.step", "vertical.level"]


def _assert_same_fields(a, b):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        np.testing.assert_array_equal(x.values, y.values)
        np.testing.assert_array_equal(x.geography.latitudes(), y.geography.latitudes())
        np.testing.assert_array_equal(x.geography.longitudes(), y.geography.longitudes())
        for k in KEYS:
            assert x.get(k) == y.get(k), k
        assert x.get("labels.param") == y.get("labels.param")
    assert [f.geography.unique_grid_id() for f in a] == [f.geography.unique_grid_id() for f in b]


def test_geopoints_fieldlist_group_date_level(tmp_path):
    fl = from_source("file", _inline(tmp_path, "param=t", rows=GROUP_ROWS)).to_fieldlist(mode="group")
    assert len(fl) == 4

    # order of first appearance, rows of a group in the order of the block
    expected = [
        (_dt(2020, 1, 1, 12), 850, [1.0, 4.0], [50.0, 53.0], [10.0, 13.0]),
        (_dt(2020, 1, 1, 12), 500, [2.0, 6.0], [51.0, 55.0], [11.0, 15.0]),
        (_dt(2020, 1, 2, 12), 850, [3.0], [52.0], [12.0]),
        (_dt(2020, 1, 2, 12), 500, [5.0], [54.0], [14.0]),
    ]
    for f, (t, level, values, lat, lon) in zip(fl, expected):
        assert f.get("time.valid_datetime") == t
        assert f.get("time.step") == datetime.timedelta(0)
        assert f.get("vertical.level") == level
        assert f.get("parameter.variable") == "t"
        assert f.values.tolist() == values
        assert f.values.dtype == np.float64
        assert f.geography.latitudes().tolist() == lat
        assert f.geography.longitudes().tolist() == lon
        assert f.geography.shape() == (len(values),)
        assert f.get("labels.param") == "t"

    r = fl.sel({"vertical.level": 500})
    assert len(r) == 2
    assert r.get("time.valid_datetime") == [_dt(2020, 1, 1, 12), _dt(2020, 1, 2, 12)]
    r = fl.sel({"vertical.level": 850, "time.valid_datetime": _dt(2020, 1, 2, 12)})
    assert len(r) == 1
    assert r[0].values.tolist() == [3.0]

    # the groups have different points
    assert len({f.geography.unique_grid_id() for f in fl}) == 4


def test_geopoints_fieldlist_group_is_partition(tmp_path):
    ds = from_source("file", _inline(tmp_path, rows=GROUP_ROWS))
    fl = ds.to_fieldlist(mode="group")
    frame = ds.to_pandas()
    assert sorted(np.concatenate([f.values for f in fl])) == sorted(frame["value"])
    assert sum(len(f.values) for f in fl) == len(frame)


def test_geopoints_fieldlist_group_ncols_value_columns(tmp_path):
    text = (
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude level date time a b\n#DATA\n"
        "50 10 850 20200101 1200 1 10\n"
        "51 11 500 20200101 1200 2 20\n"
        "52 12 850 20200101 1200 3 30\n"
    )
    fl = from_source("file", _write(tmp_path, text)).to_fieldlist(mode="group")
    # block -> group -> value column
    assert fl.get("parameter.variable") == ["a", "b", "a", "b"]
    assert fl.get("vertical.level") == [850, 850, 500, 500]
    assert [f.values.tolist() for f in fl] == [[1.0, 3.0], [10.0, 30.0], [2.0], [20.0]]


def test_geopoints_fieldlist_group_traditional():
    # all rows have the same date and level: the same as block mode
    block = _fieldlist("traditional.gpt")
    group = _fieldlist("traditional.gpt", mode="group")
    assert len(group) == 1
    _assert_same_fields(block, group)
    assert group[0].get("time.valid_datetime") == _dt(2010, 8, 10, 12, 0)
    assert group[0].get("vertical.level") == 0
    frame = from_source("file", _data_file("traditional.gpt")).to_pandas()
    np.testing.assert_array_equal(group[0].values, frame["value"].to_numpy())


@pytest.mark.parametrize(
    "name",
    [
        "traditional.gpt",
        "xyv.gpt",
        "xy_vector.gpt",
        "polar_vector.gpt",
        "metadata.gpt",
    ],
)
def test_geopoints_fieldlist_group_same_as_block(name):
    _assert_same_fields(_fieldlist(name), _fieldlist(name, mode="group"))


@pytest.mark.parametrize("name", GEOPOINTS_FILES)
def test_geopoints_fieldlist_group_all_files(name):
    ds = from_source("file", _data_file(name))
    block = ds.to_fieldlist()
    group = ds.to_fieldlist(mode="group")
    assert len(group) >= len(block)

    # the rows of the groups are the rows of the blocks
    n_block = sum(len(f.values) for f in block)
    assert sum(len(f.values) for f in group) == n_block
    for f in group:
        assert f.geography.latitudes().shape == f.values.shape

    # no grouping columns: block mode
    _assert_same_fields(block, ds.to_fieldlist(mode="group", group_by=[]))


def test_geopoints_fieldlist_group_set_blocks(tmp_path):
    # the groups of each block of a set, block by block
    text = (
        "#GEOPOINTSET\n"
        "#GEO\n#DATA\n50 10 850 20200101 1200 1\n51 11 850 20200102 1200 2\n"
        "#GEO\n#DATA\n52 12 500 20200101 1200 3\n"
        "#GEO\n#DATA\n53 13 500 20200101 1200 4\n54 14 700 20200101 1200 5\n"
    )
    fl = from_source("file", _write(tmp_path, text, "set.gpts")).to_fieldlist(mode="group")
    assert [f.values.tolist() for f in fl] == [[1.0], [2.0], [3.0], [4.0], [5.0]]
    assert fl.get("vertical.level") == [850, 850, 500, 500, 700]


def test_geopoints_fieldlist_group_by_stnid():
    fl = _fieldlist("ncols_stnid.gpt", mode="group", group_by=["stnid"])
    frame = from_source("file", _data_file("ncols_stnid.gpt")).to_pandas()
    assert len(frame) == 4
    # 4 stations x 3 value columns, station by station
    assert len(fl) == 12
    assert fl.get("labels.stnid") == [s for s in frame["stnid"] for _ in range(3)]
    assert fl.get("parameter.variable") == ["_v1", "_v2", "_v3"] * 4
    for i in range(4):
        for j, name in enumerate(["_v1", "_v2", "_v3"]):
            f = fl[3 * i + j]
            assert f.values.tolist() == [frame[name].iloc[i]]
            assert f.geography.latitudes().tolist() == [frame["latitude"].iloc[i]]
            assert f.geography.longitudes().tolist() == [frame["longitude"].iloc[i]]
            # time and level of the first (only) row
            assert f.get("vertical.level") == frame["level"].iloc[i]
            assert f.get("time.valid_datetime") == frame["date"].iloc[i].to_pydatetime()

    r = fl.sel({"labels.stnid": "texas"})
    assert len(r) == 3


def test_geopoints_fieldlist_group_by_stnid_several_rows(tmp_path):
    text = (
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nstnid latitude longitude level date time a\n#DATA\n"
        "abc 50 10 850 20200101 1200 1\n"
        "xyz 51 11 850 20200101 1200 2\n"
        "abc 50 10 700 20200102 0600 3\n"
        "abc 50 10 500 20200102 1800 4\n"
        "xyz 51 11 500 20200103 1800 5\n"
    )
    path = _write(tmp_path, text)
    fl = from_source("file", path).to_fieldlist(mode="group", group_by=["stnid"])
    assert len(fl) == 2
    assert fl.get("labels.stnid") == ["abc", "xyz"]
    assert [f.values.tolist() for f in fl] == [[1.0, 3.0, 4.0], [2.0, 5.0]]
    # time and level from the first row of the group
    assert fl.get("time.valid_datetime") == [_dt(2020, 1, 1, 12), _dt(2020, 1, 1, 12)]
    assert fl.get("vertical.level") == [850, 850]
    # python types
    assert type(fl[0].get("labels.stnid")) is str

    # the default keys give 4 groups (the first two rows share date and level), the station is no label
    fl = from_source("file", path).to_fieldlist(mode="group")
    assert len(fl) == 4
    assert fl.get("labels.stnid") == [None] * 4

    # a single name is a list with one name
    fl2 = from_source("file", path).to_fieldlist(mode="group", group_by="stnid")
    _assert_same_fields(from_source("file", path).to_fieldlist(mode="group", group_by=["stnid"]), fl2)


def test_geopoints_fieldlist_group_by_elevation(tmp_path):
    text = (
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude elevation level date time a\n#DATA\n"
        "50 10 100 850 20200101 1200 1\n"
        "51 11 200 850 20200101 1200 2\n"
        "52 12 100 850 20200101 1200 3\n"
    )
    fl = from_source("file", _write(tmp_path, text)).to_fieldlist(mode="group", group_by=["elevation"])
    assert [f.values.tolist() for f in fl] == [[1.0, 3.0], [2.0]]
    assert fl.get("labels.elevation") == [100, 200]
    # plain Python values, not numpy scalars
    assert all(type(x) in (int, float) for x in fl.get("labels.elevation"))


def test_geopoints_fieldlist_group_by_level_takes_time_from_first_row(tmp_path):
    rows = [
        "50 10 850 20200102 1200 1",
        "51 11 500 20200101 1200 2",
        "52 12 850 20200101 1200 3",
        "53 13 500 20200103 0600 4",
    ]
    fl = from_source("file", _inline(tmp_path, rows=rows)).to_fieldlist(mode="group", group_by=["level"])
    assert len(fl) == 2
    assert fl.get("vertical.level") == [850, 500]
    assert fl.get("time.valid_datetime") == [_dt(2020, 1, 2, 12), _dt(2020, 1, 1, 12)]
    assert [f.values.tolist() for f in fl] == [[1.0, 3.0], [2.0, 4.0]]
    # level is a key, so it is no label
    assert fl.get("labels.level") == [None, None]


def test_geopoints_fieldlist_group_by_date_only(tmp_path):
    fl = from_source("file", _inline(tmp_path, rows=GROUP_ROWS)).to_fieldlist(mode="group", group_by=["date"])
    assert len(fl) == 2
    assert fl.get("time.valid_datetime") == [_dt(2020, 1, 1, 12), _dt(2020, 1, 2, 12)]
    # the level of the first row
    assert fl.get("vertical.level") == [850, 850]
    assert [len(f.values) for f in fl] == [4, 2]


def test_geopoints_fieldlist_group_by_duplicates(tmp_path):
    path = _inline(tmp_path, rows=GROUP_ROWS)
    a = from_source("file", path).to_fieldlist(mode="group", group_by=["level", "level"])
    b = from_source("file", path).to_fieldlist(mode="group", group_by=["level"])
    _assert_same_fields(a, b)


def test_geopoints_fieldlist_group_by_labels(tmp_path):
    text = (
        "#GEO\n#FORMAT NCOLS\n#METADATA\nparam=t\nstnid=meta\nother=7\n#COLUMNS\n"
        "stnid latitude longitude level date time a\n#DATA\n"
        "abc 50 10 850 20200101 1200 1\n"
        "xyz 51 11 850 20200101 1200 2\n"
    )
    fl = from_source("file", _write(tmp_path, text)).to_fieldlist(mode="group", group_by=["stnid"])
    # the group key wins over the #METADATA pair, the other pairs stay
    assert fl.get("labels.stnid") == ["abc", "xyz"]
    assert fl.get("labels.param") == ["t", "t"]
    assert fl.get("labels.other") == [7, 7]


def test_geopoints_fieldlist_group_by_unknown_column(tmp_path):
    path = _inline(tmp_path, rows=GROUP_ROWS)
    with pytest.raises(ValueError, match="nothing") as e:
        from_source("file", path).to_fieldlist(mode="group", group_by=["nothing"])
    assert "test.gpt" in str(e.value)

    # stnid does not exist in a traditional block
    with pytest.raises(ValueError, match="stnid"):
        from_source("file", path).to_fieldlist(mode="group", group_by=["level", "stnid"])

    # the file is named for the second file of a list
    other = _write(
        tmp_path, "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude stnid a\n#DATA\n50 10 s 1\n", "other.gpt"
    )
    ds = from_source("file", [other, path])
    with pytest.raises(ValueError, match="test.gpt"):
        ds.to_fieldlist(mode="group", group_by=["stnid"])


@pytest.mark.parametrize("group_by", [1, [1], [None], 1.5])
def test_geopoints_fieldlist_group_by_bad_type(tmp_path, group_by):
    with pytest.raises(ValueError, match="group_by"):
        from_source("file", _inline(tmp_path)).to_fieldlist(mode="group", group_by=group_by)


def test_geopoints_fieldlist_group_nat_nan_keys(tmp_path):
    rows = [
        "50 10 850 20200101 1200 1",
        "51 11 3e+38 20200101 1200 2",
        "52 12 850 0 0 3",
        "53 13 3e+38 20200101 1200 4",
        "54 14 850 0 0 5",
        "55 15 3e+38 0 0 6",
    ]
    fl = from_source("file", _inline(tmp_path, "level=5\ndate=19990101\ntime=0000", rows=rows)).to_fieldlist(
        mode="group"
    )
    assert len(fl) == 4
    assert [f.values.tolist() for f in fl] == [[1.0], [2.0, 4.0], [3.0, 5.0], [6.0]]
    # NaN level: no level; NaT date: no time (the #METADATA is not used for a block with a date column)
    assert fl.get("vertical.level") == [850, None, 850, None]
    assert fl.get("time.valid_datetime") == [_dt(2020, 1, 1, 12), _dt(2020, 1, 1, 12), None, None]
    assert fl.get("time.base_datetime") == [_dt(2020, 1, 1, 12), _dt(2020, 1, 1, 12), None, None]

    # only the date
    fl = from_source("file", _inline(tmp_path, rows=rows)).to_fieldlist(mode="group", group_by=["date"])
    assert [f.values.tolist() for f in fl] == [[1.0, 2.0, 4.0], [3.0, 5.0, 6.0]]
    assert fl.get("time.valid_datetime") == [_dt(2020, 1, 1, 12), None]

    # only the level: the NaN rows are a group
    fl = from_source("file", _inline(tmp_path, rows=rows)).to_fieldlist(mode="group", group_by=["level"])
    assert [f.values.tolist() for f in fl] == [[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]]
    assert fl.get("vertical.level") == [850, None]


def test_geopoints_fieldlist_group_nan_other_key(tmp_path):
    text = (
        "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude elevation a\n#DATA\n"
        "50 10 100 1\n51 11 3e+38 2\n52 12 100 3\n53 13 3e+38 4\n"
    )
    fl = from_source("file", _write(tmp_path, text)).to_fieldlist(mode="group", group_by=["elevation"])
    assert [f.values.tolist() for f in fl] == [[1.0, 3.0], [2.0, 4.0]]
    # no label for a missing value
    assert fl.get("labels.elevation") == [100, None]


def test_geopoints_fieldlist_group_xyv():
    # no date, no level: the whole block is one group
    _assert_same_fields(_fieldlist("xyv.gpt"), _fieldlist("xyv.gpt", mode="group"))
    f = _fieldlist("xyv.gpt", mode="group")[0]
    assert f.get("time.valid_datetime") is None
    assert f.get("vertical.level") is None


def test_geopoints_fieldlist_group_xyv_metadata(tmp_path):
    path = _write(
        tmp_path,
        "#GEO\n#FORMAT XYV\n#METADATA\nparam=t\ndate=20130804\ntime=0600\nlevel=500\n#DATA\n10 50 1\n11 51 2\n",
    )
    fl = from_source("file", path).to_fieldlist(mode="group")
    _assert_same_fields(from_source("file", path).to_fieldlist(), fl)
    assert fl[0].get("time.valid_datetime") == _dt(2013, 8, 4, 6, 0)
    assert fl[0].get("vertical.level") == 500


def test_geopoints_fieldlist_group_by_empty_list(tmp_path):
    path = _inline(tmp_path, "param=t", rows=GROUP_ROWS)
    block = from_source("file", path).to_fieldlist()
    group = from_source("file", path).to_fieldlist(mode="group", group_by=[])
    assert len(group) == 1
    _assert_same_fields(block, group)
    assert group[0].values.tolist() == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_geopoints_fieldlist_group_by_empty_tuple_ncols():
    _assert_same_fields(_fieldlist("ncols_stnid.gpt"), _fieldlist("ncols_stnid.gpt", mode="group", group_by=()))


def test_geopoints_fieldlist_group_single_group_with_key_label(tmp_path):
    # one group, but the key is still a label
    text = "#GEO\n#FORMAT NCOLS\n#COLUMNS\nstnid latitude longitude a\n#DATA\nabc 50 10 1\nabc 51 11 2\n"
    fl = from_source("file", _write(tmp_path, text)).to_fieldlist(mode="group", group_by=["stnid"])
    assert len(fl) == 1
    assert fl[0].get("labels.stnid") == "abc"
    assert fl[0].values.tolist() == [1.0, 2.0]


def test_geopoints_fieldlist_group_metadata_step(tmp_path):
    fl = from_source("file", _inline(tmp_path, "step=6", rows=GROUP_ROWS)).to_fieldlist(mode="group")
    assert len(fl) == 4
    for f in fl:
        assert f.get("time.step") == datetime.timedelta(hours=6)
        assert f.get("time.base_datetime") == f.get("time.valid_datetime") - datetime.timedelta(hours=6)


def test_geopoints_fieldlist_group_empty_block(tmp_path):
    path = _write(tmp_path, "#GEOPOINTSET\n#GEO\n#DATA\n#GEO\n#DATA\n50 10 0 20200101 1200 1\n")
    fl = from_source("file", path).to_fieldlist(mode="group")
    assert len(fl) == 1
    assert len(from_source("file", _write(tmp_path, "#GEOPOINTSET\n", "e.gpts")).to_fieldlist(mode="group")) == 0


def test_geopoints_fieldlist_group_text_column_warns_once_per_block(tmp_path):
    rows = ["50 10 850 20200101 1200 abc", "51 11 500 20200101 1200 x", "52 12 700 20200101 1200 y"]
    with pytest.warns(UserWarning, match="test.gpt") as w:
        fl = from_source("file", _inline(tmp_path, rows=rows)).to_fieldlist(mode="group")
    assert len(fl) == 0
    assert len([x for x in w if "not numeric" in str(x.message)]) == 1


def test_geopoints_fieldlist_group_two_files(tmp_path):
    p1 = _inline(tmp_path, "param=t", rows=GROUP_ROWS)
    p2 = _write(
        tmp_path,
        "#GEOPOINTSET\n"
        "#GEO\n#DATA\n50 10 100 20200301 0000 7\n51 11 200 20200301 0000 8\n"
        "#GEO\n#DATA\n52 12 300 20200302 0000 9\n",
        "second.gpts",
    )
    ds = from_source("file", [p1, p2])
    assert ds._reader.is_multi
    fl = ds.to_fieldlist(mode="group")

    a = from_source("file", p1).to_fieldlist(mode="group")
    b = from_source("file", p2).to_fieldlist(mode="group")
    assert len(a) == 4 and len(b) == 3
    assert len(fl) == 7
    for x, y in zip(fl, list(a) + list(b)):
        np.testing.assert_array_equal(x.values, y.values)
        assert x.get("time.valid_datetime") == y.get("time.valid_datetime")
        assert x.get("vertical.level") == y.get("vertical.level")
    assert fl.get("vertical.level") == [850, 500, 850, 500, 100, 200, 300]

    # group_by is applied to every file
    fl = ds.to_fieldlist(mode="group", group_by=["level"])
    assert fl.get("vertical.level") == [850, 500, 100, 200, 300]


def test_geopoints_fieldlist_group_ls(tmp_path):
    fl = from_source("file", _inline(tmp_path, rows=GROUP_ROWS)).to_fieldlist(mode="group")
    df = fl.ls()
    assert len(df) == 4
    assert df["vertical.level"].tolist() == [850, 500, 850, 500]


def test_geopoints_fieldlist_group_to_xarray_one_group(tmp_path):
    # fields of different groups have different points
    fl = from_source("file", _inline(tmp_path, rows=GROUP_ROWS)).to_fieldlist(mode="group")
    with pytest.raises(ValueError, match="same grid"):
        fl.to_xarray()


def test_geopoints_fieldlist_group_values_are_independent(tmp_path):
    ds = from_source("file", _inline(tmp_path, rows=GROUP_ROWS))
    fl = ds.to_fieldlist(mode="group")
    fl[0].values[0] = -1
    assert ds.to_pandas()["value"].tolist() == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    # the second call gives fresh values
    assert ds.to_fieldlist(mode="group")[0].values[0] == 1.0


def test_geopoints_fieldlist_group_does_not_change_block(tmp_path):
    ds = from_source("file", _inline(tmp_path, rows=GROUP_ROWS))
    before = ds.to_pandas()
    ds.to_fieldlist(mode="group", group_by=["level"])
    after = ds.to_pandas()
    assert before.equals(after)
