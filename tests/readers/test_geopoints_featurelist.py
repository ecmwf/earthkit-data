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
import pickle

import pandas as pd
import pytest

from earthkit.data import from_source
from earthkit.data.data.featurelist import FeatureListData
from earthkit.data.data.geopoints import GeopointsData
from earthkit.data.readers.geopoints.featurelist import (
    GeopointsFeature,
    GeopointsFeatureList,
    GeopointsRowFeature,
    GeopointsRowFeatureList,
    make_featurelist,
)
from earthkit.data.readers.geopoints.parser import GeopointsBlock
from earthkit.data.utils.testing import earthkit_test_data_file

GEOPOINTS_FILES = sorted(os.listdir(earthkit_test_data_file("geopoints")))

# a block without #METADATA, a block with it, another block without it
SET_PARAMS = [None, "geopotential", None]


def _data_file(name):
    return earthkit_test_data_file("geopoints", name)


def _write(tmp_path, text, name="test.gpt"):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def _featurelist(name, **kwargs):
    return from_source("file", _data_file(name)).to_featurelist(**kwargs)


def _params(fl):
    return fl.metadata("param", default=None)


# -- creation ---------------------------------------------------------------------------------


@pytest.mark.parametrize("name", GEOPOINTS_FILES)
def test_geopoints_featurelist_all_files(name):
    ds = from_source("file", _data_file(name))
    fl = ds.to_featurelist()
    assert isinstance(fl, GeopointsFeatureList)
    n = 3 if name == "geopointset.gpts" else 1
    assert len(fl) == n
    assert all(isinstance(f, GeopointsFeature) for f in fl)
    assert sum(len(f) for f in fl) == len(ds.to_pandas())
    pd.testing.assert_frame_equal(fl.to_pandas(), ds.to_pandas())


def test_geopoints_featurelist_mode_block_is_default():
    ds = from_source("file", _data_file("geopointset.gpts"))
    fl1 = ds.to_featurelist()
    fl2 = ds.to_featurelist(mode="block")
    assert len(fl1) == len(fl2) == 3
    assert _params(fl1) == _params(fl2)
    # the reader gives the same
    assert len(ds._reader.to_featurelist()) == 3
    assert len(ds._reader.to_featurelist(mode="block")) == 3


@pytest.mark.parametrize("mode", ["bad", "", None, 1, "BLOCK"])
def test_geopoints_featurelist_invalid_mode(mode):
    ds = from_source("file", _data_file("traditional.gpt"))
    with pytest.raises(ValueError, match="'block', 'row'"):
        ds.to_featurelist(mode=mode)
    with pytest.raises(ValueError, match="'block', 'row'"):
        ds._reader.to_featurelist(mode=mode)


def test_geopoints_featurelist_available_types():
    d = from_source("file", _data_file("traditional.gpt"))
    assert d.available_types == ["pandas", "xarray", "featurelist"]
    assert GeopointsData._FEATURELIST == "featurelist"


def test_geopoints_featurelist_empty_set(tmp_path):
    ds = from_source("file", _write(tmp_path, "#GEOPOINTSET\n", "empty.gpts"))
    fl = ds.to_featurelist()
    assert len(fl) == 0
    assert list(fl) == []
    assert fl.metadata("param", default=None) == []
    assert fl.metadata() == []
    df = fl.to_pandas()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert len(df.columns) == 0
    assert len(fl.sel(param="a")) == 0
    assert len(fl.order_by("param")) == 0
    assert len(fl.ls()) == 0
    assert len(fl.head()) == 0
    assert len(fl.tail()) == 0
    assert len(fl.to_xarray().data_vars) == 0
    with pytest.raises(IndexError):
        fl[0]


def test_geopoints_featurelist_block_without_rows(tmp_path):
    ds = from_source("file", _write(tmp_path, "#GEO\n#METADATA\nparam=t\n#DATA\n"))
    fl = ds.to_featurelist()
    assert len(fl) == 1
    f = fl[0]
    assert len(f) == 0
    assert f.metadata() == {"param": "t"}
    assert f.columns == ["latitude", "longitude", "level", "date", "time", "value"]
    df = f.to_pandas()
    assert len(df) == 0
    assert list(df.columns) == ["latitude", "longitude", "level", "date", "value"]
    assert len(fl.to_pandas()) == 0


def test_geopoints_featurelist_set_with_empty_block(tmp_path):
    text = "#GEOPOINTSET\n#GEO\n#DATA\n1 2 0 20130512 0 3.0\n#GEO\n#METADATA\nparam=t\n#DATA\n"
    fl = from_source("file", _write(tmp_path, text, "nodata.gpts")).to_featurelist()
    assert [len(f) for f in fl] == [1, 0]
    assert len(fl.to_pandas()) == 1


# -- feature ----------------------------------------------------------------------------------


def test_geopoints_feature_metadata_all():
    f = _featurelist("metadata.gpt")[0]
    assert f.metadata() == {"param": "temperature", "date": 20130804, "time": 1200, "level": 0.2}
    types = {k: type(v) for k, v in f.metadata().items()}
    assert types == {"param": str, "date": int, "time": int, "level": float}


def test_geopoints_feature_metadata_no_metadata():
    f = _featurelist("traditional.gpt")[0]
    assert f.metadata() == {}
    assert f.default_ls_keys == []
    with pytest.raises(KeyError):
        f.metadata("param")


def test_geopoints_feature_metadata_forms():
    f = _featurelist("metadata.gpt")[0]
    assert f.metadata("param") == "temperature"
    assert f.metadata("level") == 0.2
    assert f.metadata(["param", "date"]) == ["temperature", 20130804]
    assert f.metadata(("param", "date")) == ["temperature", 20130804]
    assert f.metadata("param", "date") == ["temperature", 20130804]
    assert f.metadata("param", ["date", "time"]) == ["temperature", 20130804, 1200]
    assert f.metadata(["param"]) == ["temperature"]
    assert f.metadata([]) == []


def test_geopoints_feature_metadata_missing_key():
    f = _featurelist("metadata.gpt")[0]
    with pytest.raises(KeyError, match="foo"):
        f.metadata("foo")
    with pytest.raises(KeyError, match="foo"):
        f.metadata(["param", "foo"])
    with pytest.raises(KeyError, match="foo"):
        f.metadata("param", "foo")


def test_geopoints_feature_metadata_default():
    f = _featurelist("metadata.gpt")[0]
    assert f.metadata("foo", default=None) is None
    assert f.metadata("foo", default=7) == 7
    assert f.metadata(["param", "foo"], default=None) == ["temperature", None]
    assert f.metadata("param", "foo", default="x") == ["temperature", "x"]
    # the default is not used when the key exists
    assert f.metadata("param", default="x") == "temperature"
    # a falsy default is a default
    assert f.metadata("foo", default=0) == 0


def test_geopoints_feature_metadata_astype():
    f = _featurelist("metadata.gpt")[0]
    assert f.metadata("date", astype=str) == "20130804"
    assert f.metadata("level", astype=int) == 0
    assert f.metadata(["date", "time"], astype=str) == ["20130804", "1200"]
    assert f.metadata(["date", "level"], astype=[str, int]) == ["20130804", 0]
    with pytest.raises(ValueError):
        f.metadata(["date", "level"], astype=[str, int, float])


def test_geopoints_feature_metadata_is_copy():
    f = _featurelist("metadata.gpt")[0]
    m = f.metadata()
    m["param"] = "changed"
    m["new"] = 1
    assert f.metadata() == {"param": "temperature", "date": 20130804, "time": 1200, "level": 0.2}
    assert f.metadata("param") == "temperature"
    assert "new" not in f.metadata()


def test_geopoints_feature_metadata_independent_of_block():
    ds = from_source("file", _data_file("metadata.gpt"))
    f = ds.to_featurelist()[0]
    ds._reader.blocks[0].metadata["param"] = "changed"
    assert f.metadata("param") == "temperature"


def test_geopoints_feature_attributes():
    f = _featurelist("metadata.gpt")[0]
    assert f.format == "TRADITIONAL"
    assert f.columns == ["latitude", "longitude", "level", "date", "time", "value"]
    assert len(f) == 44
    # attributes are not metadata keys
    for k in ("format", "columns"):
        assert f.metadata(k, default=None) is None

    f.columns.append("x")
    assert f.columns == ["latitude", "longitude", "level", "date", "time", "value"]

    f = _featurelist("ncols_stnid.gpt")[0]
    assert f.format == "NCOLS"
    # the column names in file order; "time" is merged into "date" in the DataFrame
    assert f.columns == ["stnid", "latitude", "time", "longitude", "level", "date", "_v1", "_v2", "_v3"]
    assert len(f) == 4

    f = _featurelist("xyv.gpt")[0]
    assert f.format == "XYV"
    assert f.columns == ["longitude", "latitude", "value"]


def test_geopoints_feature_to_pandas():
    ds = from_source("file", _data_file("metadata.gpt"))
    f = ds.to_featurelist()[0]
    df = f.to_pandas()
    pd.testing.assert_frame_equal(df, ds.to_pandas())
    assert len(df) == len(f)

    # a copy
    df.loc[0, "value"] = -1.0
    df["extra"] = 1
    df2 = f.to_pandas()
    assert df2.loc[0, "value"] == 294.4
    assert "extra" not in df2.columns


def test_geopoints_feature_to_xarray():
    import xarray as xr

    ds = from_source("file", _data_file("traditional.gpt"))
    f = ds.to_featurelist()[0]
    x = f.to_xarray()
    assert isinstance(x, xr.Dataset)
    assert set(x.data_vars) == {"latitude", "longitude", "level", "date", "value"}
    assert x["value"].shape == (8,)
    xr.testing.assert_identical(x, ds.to_xarray())

    with pytest.raises(TypeError):
        f.to_xarray(foo=1)


def test_geopoints_feature_repr():
    f = _featurelist("metadata.gpt")[0]
    assert repr(f) == (
        "GeopointsFeature(format='TRADITIONAL', points=44, "
        "metadata={'param': 'temperature', 'date': 20130804, 'time': 1200, 'level': 0.2})"
    )

    f = _featurelist("ncols.gpt")[0]
    assert repr(f) == "GeopointsFeature(format='NCOLS', points=4, metadata={})"


def test_geopoints_feature_internal_access():
    f = _featurelist("metadata.gpt")[0]
    assert f._default_encoder() is None
    assert f.default_ls_keys == ["param", "date", "time", "level"]

    assert f._get_single("param") == "temperature"
    assert f._get_single("foo") is None
    assert f._get_single("foo", default=3) == 3
    assert f._get_single("date", astype=str) == "20130804"
    with pytest.raises(KeyError):
        f._get_single("foo", raise_on_missing=True)

    assert f._get_fast("param") == "temperature"
    assert f._get_fast("param", output=dict) == {"param": "temperature"}
    assert f._get_fast(["param", "foo"], default=[None, None], astype=[None, None]) == ["temperature", None]
    assert f._get_fast(["param", "foo"], default=None) == ["temperature", None]
    assert f._get_fast(("param", "level"), output=tuple) == ("temperature", 0.2)
    assert f._get_fast(
        keys=["param", "foo"],
        default=[None, 1],
        astype=[None, None],
        collections=None,
        output=dict,
        flatten_dict=True,
    ) == {"param": "temperature", "foo": 1}
    assert f._get_fast(None, output=dict) == {}
    with pytest.raises(KeyError):
        f._get_fast(["param", "foo"], raise_on_missing=True)


# -- list: indexing and iteration --------------------------------------------------------------


def test_geopoints_featurelist_indexing():
    fl = _featurelist("geopointset.gpts")
    assert len(fl) == 3
    assert [len(f) for f in fl] == [4, 1, 3]

    assert fl[0].metadata() == {}
    assert fl[1].metadata() == {"param": "geopotential"}
    assert fl[2].metadata() == {}
    assert fl[-1] is fl[2]
    assert fl[-3] is fl[0]
    assert fl[1] is fl[1]

    with pytest.raises(IndexError):
        fl[3]
    with pytest.raises(IndexError):
        fl[-4]


def test_geopoints_featurelist_slicing():
    fl = _featurelist("geopointset.gpts")

    s = fl[1:]
    assert isinstance(s, GeopointsFeatureList)
    assert len(s) == 2
    assert s[0] is fl[1]
    assert s[1] is fl[2]
    assert [len(f) for f in s] == [1, 3]

    s = fl[::2]
    assert [len(f) for f in s] == [4, 3]

    s = fl[::-1]
    assert [len(f) for f in s] == [3, 1, 4]

    assert len(fl[5:]) == 0
    assert len(fl[:]) == 3

    s = fl[[0, 2]]
    assert isinstance(s, GeopointsFeatureList)
    assert [len(f) for f in s] == [4, 3]


def test_geopoints_featurelist_slice_of_slice():
    fl = _featurelist("geopointset.gpts")
    s = fl[1:][1:]
    assert isinstance(s, GeopointsFeatureList)
    assert len(s) == 1
    assert s[0] is fl[2]

    s = fl[::-1][:2]
    assert [len(f) for f in s] == [3, 1]
    assert s[-1] is fl[1]

    with pytest.raises(IndexError):
        fl[1:][2]


def test_geopoints_featurelist_iteration():
    fl = _featurelist("geopointset.gpts")
    features = list(fl)
    assert len(features) == 3
    assert all(isinstance(f, GeopointsFeature) for f in features)
    assert [f is fl[i] for i, f in enumerate(features)] == [True] * 3
    assert [len(f) for f in fl[1:]] == [1, 3]
    assert [f.metadata("param", default=None) for f in fl] == SET_PARAMS


def test_geopoints_featurelist_pickle():
    fl = _featurelist("geopointset.gpts")
    fl2 = pickle.loads(pickle.dumps(fl))
    assert isinstance(fl2, GeopointsFeatureList)
    assert len(fl2) == 3
    assert _params(fl2) == SET_PARAMS
    pd.testing.assert_frame_equal(fl2.to_pandas(), fl.to_pandas())


# -- list: sel --------------------------------------------------------------------------------


def test_geopoints_featurelist_sel():
    fl = _featurelist("geopointset.gpts")
    r = fl.sel(param="geopotential")
    assert isinstance(r, GeopointsFeatureList)
    assert len(r) == 1
    assert r[0] is fl[1]
    assert r.metadata("param") == ["geopotential"]

    assert len(fl.sel(param="nothing")) == 0
    assert len(fl.sel(param=["geopotential", "temperature"])) == 1
    assert len(fl.sel({"param": "geopotential"})) == 1
    # a block without the key does not match
    assert len(fl.sel(foo="geopotential")) == 0


def test_geopoints_featurelist_sel_typed_values():
    fl = _featurelist("metadata.gpt")
    assert len(fl.sel(date=20130804)) == 1
    assert len(fl.sel(date=20130805)) == 0
    assert len(fl.sel(level=0.2)) == 1
    assert len(fl.sel(time=slice(1000, 1300))) == 1
    assert len(fl.sel(param="temperature", date=20130804, time=1200)) == 1
    assert len(fl.sel(param="temperature", date=20130805)) == 0


def test_geopoints_featurelist_sel_on_slice():
    fl = _featurelist("geopointset.gpts")
    r = fl[1:].sel(param="geopotential")
    assert isinstance(r, GeopointsFeatureList)
    assert len(r) == 1
    assert r[0] is fl[1]

    assert len(fl[2:].sel(param="geopotential")) == 0
    # a slice of a sel result
    assert len(fl.sel(param="geopotential")[1:]) == 0
    assert fl.sel(param="geopotential")[-1] is fl[1]


def test_geopoints_featurelist_sel_remapping():
    fl = _featurelist("metadata.gpt")
    r = fl.sel(pd="temperature20130804", remapping={"pd": "{param}{date}"})
    assert len(r) == 1
    assert len(fl.sel(pd="temperature20130805", remapping={"pd": "{param}{date}"})) == 0


# -- list: order_by ---------------------------------------------------------------------------


def test_geopoints_featurelist_order_by_missing_last():
    fl = _featurelist("geopointset.gpts")
    assert _params(fl) == SET_PARAMS

    # the missing values keep their relative order (stable sort)
    r = fl.order_by("param")
    assert isinstance(r, GeopointsFeatureList)
    assert _params(r) == ["geopotential", None, None]
    assert [len(f) for f in r] == [1, 4, 3]

    r = fl.order_by(param="ascending")
    assert [len(f) for f in r] == [1, 4, 3]

    r = fl.order_by(param="descending")
    assert _params(r) == ["geopotential", None, None]
    assert [len(f) for f in r] == [1, 4, 3]

    r = fl.order_by({"param": "descending"})
    assert [len(f) for f in r] == [1, 4, 3]

    r = fl.order_by(["param"])
    assert [len(f) for f in r] == [1, 4, 3]

    # the original is unchanged
    assert _params(fl) == SET_PARAMS


def test_geopoints_featurelist_order_by_values():
    fl = _featurelist("geopointset.gpts")
    # the list of values, missing last
    r = fl.order_by(param=["temperature", "geopotential"])
    assert _params(r) == ["geopotential", None, None]


def test_geopoints_featurelist_order_by_slice_and_chain():
    fl = _featurelist("geopointset.gpts")
    r = fl[::-1].order_by("param")
    assert [len(f) for f in r] == [1, 3, 4]
    r = fl.order_by("param")[:2]
    assert [len(f) for f in r] == [1, 4]


def _block(**metadata):
    return GeopointsBlock("TRADITIONAL", ["latitude"], metadata, pd.DataFrame({"latitude": [1.0]}))


def test_geopoints_featurelist_order_by_nan_none_and_numbers():
    nan = float("nan")
    values = [3, None, 1.5, nan, 2, "absent"]
    blocks = [_block(v=v) if v != "absent" else _block() for v in values]
    fl = GeopointsFeatureList([GeopointsFeature(b) for b in blocks])

    def vals(x):
        return [f.metadata("v", default=None) for f in x]

    r = fl.order_by("v")
    assert vals(r)[:3] == [1.5, 2, 3]
    assert all(v is None or v != v for v in vals(r)[3:])
    assert len(vals(r)) == 6

    r = fl.order_by(v="descending")
    assert vals(r)[:3] == [3, 2, 1.5]
    assert all(v is None or v != v for v in vals(r)[3:])


def test_geopoints_featurelist_order_by_several_keys():
    blocks = [
        _block(a=2, b="x"),
        _block(a=1, b="y"),
        _block(a=2, b="a"),
        _block(a=1),
        _block(b="z"),
    ]
    fl = GeopointsFeatureList([GeopointsFeature(b) for b in blocks])

    r = fl.order_by("a", "b")
    assert r.metadata("a", "b", default=None) == [
        [1, "y"],
        [1, None],
        [2, "a"],
        [2, "x"],
        [None, "z"],
    ]

    r = fl.order_by(a="descending", b="ascending")
    assert r.metadata("a", "b", default=None) == [
        [2, "a"],
        [2, "x"],
        [1, "y"],
        [1, None],
        [None, "z"],
    ]


def test_geopoints_featurelist_order_by_callable():
    fl = _featurelist("geopointset.gpts")
    r = fl.order_by(param=lambda a, b: 0)
    assert [len(f) for f in r] == [4, 1, 3]


def _distance_from_5(a, b):
    # custom order: the closer to 5 the earlier
    return abs(a - 5) - abs(b - 5)


def test_geopoints_featurelist_order_by_callable_custom_order(tmp_path):
    # one block per value of k, in the order 9, 1, 4, 5, 7, 2
    ks = [9, 1, 4, 5, 7, 2]
    path = _write(
        tmp_path,
        "#GEOPOINTSET\n" + "".join(f"#GEO\n#METADATA\nk={k}\n#DATA\n10 20 0 20130101 1200 {k}\n" for k in ks),
        "custom.gpts",
    )
    ds = from_source("file", path)

    blocks = ds.to_featurelist()
    assert blocks.metadata("k") == ks
    # distance from 5: 9->4, 1->4, 4->1, 5->0, 7->2, 2->3 (the sort is stable)
    expected = [5, 4, 7, 2, 9, 1]
    assert blocks.order_by(k=_distance_from_5).metadata("k") == expected
    assert blocks.order_by(k=lambda a, b: _distance_from_5(b, a)).metadata("k") == [9, 1, 2, 7, 4, 5]
    # a chain
    assert blocks.order_by(k=_distance_from_5)[:3].metadata("k") == expected[:3]
    assert blocks[1:].order_by(k=_distance_from_5).metadata("k") == [5, 4, 7, 2, 1]

    # the callable gets the raw values
    seen = set()

    def cmp(a, b):
        seen.update([type(a), type(b)])
        return a - b

    assert blocks.order_by(k=cmp).metadata("k") == sorted(ks)
    assert seen == {int}

    # the same for the rows (one row per block here)
    rows = ds.to_featurelist(mode="row")
    r = rows.order_by(value=_distance_from_5)
    assert isinstance(r, GeopointsRowFeatureList)
    assert r.metadata("value") == expected
    assert rows.order_by(k=_distance_from_5)[1:3].metadata("k") == expected[1:3]


def test_geopoints_featurelist_order_by_no_keys():
    fl = _featurelist("geopointset.gpts")
    assert fl.order_by() is fl


# -- list: metadata, get, ls ------------------------------------------------------------------


def test_geopoints_featurelist_metadata():
    fl = _featurelist("geopointset.gpts")
    assert fl.metadata("param", default=None) == SET_PARAMS
    assert fl.metadata() == [{}, {"param": "geopotential"}, {}]
    assert fl.metadata(["param"], default="n/a") == [["n/a"], ["geopotential"], ["n/a"]]
    assert fl[1:].metadata("param", default=None) == ["geopotential", None]

    with pytest.raises(KeyError):
        fl.metadata("param")

    fl = _featurelist("metadata.gpt")
    assert fl.metadata("date", "time") == [[20130804, 1200]]
    assert fl.metadata("date", astype=str) == ["20130804"]


def test_geopoints_featurelist_get():
    fl = _featurelist("geopointset.gpts")
    assert fl.get("param") == SET_PARAMS
    assert fl.get("param", default="n/a") == ["n/a", "geopotential", "n/a"]
    assert fl.get(["param"]) == [[None], ["geopotential"], [None]]
    assert fl.get(["param", "foo"], default=0) == [[0, 0], ["geopotential", 0], [0, 0]]
    assert fl.get("param", output=dict) == [{"param": v} for v in SET_PARAMS]
    with pytest.raises(KeyError):
        fl.get("param", raise_on_missing=True)


def test_geopoints_featurelist_ls():
    fl = _featurelist("metadata.gpt")
    df = fl.ls()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["param", "date", "time", "level"]
    assert df.iloc[0].tolist() == ["temperature", 20130804, 1200, 0.2]

    df = fl.ls(keys=["level", "param"])
    assert list(df.columns) == ["level", "param"]
    assert len(df) == 1

    df = fl.ls(keys="default", extra_keys=["foo"])
    assert list(df.columns) == ["param", "date", "time", "level", "foo"]
    assert df.iloc[0]["foo"] is None


def test_geopoints_featurelist_ls_set():
    fl = _featurelist("geopointset.gpts")

    # the default keys are the union of the keys of the features, the first one has no metadata
    df = fl.ls()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["param"]
    assert df["param"].tolist() == SET_PARAMS

    df = fl.ls(keys=["param"])
    assert df["param"].tolist() == SET_PARAMS

    df = fl[1:].ls()
    assert list(df.columns) == ["param"]
    assert df["param"].tolist() == ["geopotential", None]

    # only the features that are shown define the columns
    assert len(fl.ls(n=1).columns) == 0
    assert list(fl.ls(n=2).columns) == ["param"]
    assert list(fl.ls(n=-1).columns) == []
    assert list(fl.ls(n=-2).columns) == ["param"]

    assert len(fl.ls(keys=["param"], n=2)) == 2
    assert len(fl.ls(keys=["param"], n=-2)) == 2
    assert fl.ls(keys=["param"], n=-1)["param"].tolist() == [None]


def test_geopoints_featurelist_head_tail():
    fl = _featurelist("geopointset.gpts")
    assert fl.head(2, keys=["param"])["param"].tolist() == [None, "geopotential"]
    assert fl.tail(2, keys=["param"])["param"].tolist() == ["geopotential", None]
    assert len(fl.head(keys=["param"])) == 3
    assert len(fl.tail(keys=["param"])) == 3
    assert len(fl.head(1, keys=["param"])) == 1
    with pytest.raises(ValueError):
        fl.head(0)
    with pytest.raises(ValueError):
        fl.tail(0)


def test_geopoints_featurelist_head_tail_default_keys():
    fl = _featurelist("geopointset.gpts")
    # the keys come only from the features that are shown
    df = fl.head(2)
    assert list(df.columns) == ["param"]
    assert df["param"].tolist() == [None, "geopotential"]
    assert len(fl.head(1).columns) == 0
    assert list(fl.tail(2).columns) == ["param"]
    assert len(fl.tail(1).columns) == 0
    assert list(fl.head().columns) == ["param"]
    assert list(fl.tail().columns) == ["param"]


def test_geopoints_featurelist_ls_union_of_keys_in_first_seen_order():
    blocks = [_block(b=1), _block(a=2, b=3), _block(c=4, a=5)]
    fl = GeopointsFeatureList([GeopointsFeature(b) for b in blocks])
    df = fl.ls()
    assert list(df.columns) == ["b", "a", "c"]
    assert df["b"].tolist()[0] == 1
    assert df["a"].tolist()[1:] == [2, 5]
    # a feature without the key has None (pandas shows it as NaN in a numeric column)
    assert pd.isna(df["a"].tolist()[0])
    assert pd.isna(df["c"].tolist()[:2]).all()
    assert fl.ls(n=1, extra_keys=["a"])["a"].tolist() == [None]
    assert list(fl.ls(n=2).columns) == ["b", "a"]
    assert list(fl.ls(n=-2).columns) == ["a", "b", "c"]
    assert list(fl.ls(extra_keys=["z"]).columns) == ["b", "a", "c", "z"]
    assert list(fl.ls(keys=["c"]).columns) == ["c"]


def test_geopoints_featurelist_ls_invalid_n():
    fl = _featurelist("metadata.gpt")
    with pytest.raises(ValueError):
        fl.ls(n=0)
    with pytest.raises(ValueError):
        fl.ls(n="a")


# -- list: conversions ------------------------------------------------------------------------


def test_geopoints_featurelist_to_pandas():
    ds = from_source("file", _data_file("geopointset.gpts"))
    fl = ds.to_featurelist()

    df = fl.to_pandas()
    pd.testing.assert_frame_equal(df, ds.to_pandas())
    assert list(df.index) == list(range(8))

    # a slice
    df = fl[1:].to_pandas()
    expected = pd.concat([fl[1].to_pandas(), fl[2].to_pandas()], ignore_index=True)
    pd.testing.assert_frame_equal(df, expected)
    assert len(df) == 4
    assert list(df.index) == list(range(4))

    df = fl[2:].to_pandas()
    pd.testing.assert_frame_equal(df, fl[2].to_pandas())

    # in the order of the list
    df = fl.sel(param="geopotential").to_pandas()
    pd.testing.assert_frame_equal(df, fl[1].to_pandas())
    df = fl.order_by("param").to_pandas()
    expected = pd.concat([fl[1].to_pandas(), fl[0].to_pandas(), fl[2].to_pandas()], ignore_index=True)
    pd.testing.assert_frame_equal(df, expected)

    assert fl[:0].to_pandas().empty


def test_geopoints_featurelist_to_pandas_different_columns(tmp_path):
    text = """#GEOPOINTSET
#GEO
#METADATA
param=t
#DATA
10.0 20.0 0 20130512 0 1.5
#GEO
#FORMAT NCOLS
#COLUMNS
latitude longitude date t2
#DATA
12.0 22.0 20130513 280.5
"""
    ds = from_source("file", _write(tmp_path, text, "mixed.gpts"))
    fl = ds.to_featurelist()
    assert [f.format for f in fl] == ["TRADITIONAL", "NCOLS"]
    pd.testing.assert_frame_equal(fl.to_pandas(), ds.to_pandas())
    assert fl.to_pandas()["t2"].isna().tolist() == [True, False]


def test_geopoints_featurelist_to_xarray():
    import xarray as xr

    ds = from_source("file", _data_file("geopointset.gpts"))
    fl = ds.to_featurelist()
    x = fl.to_xarray()
    assert isinstance(x, xr.Dataset)
    assert set(x.data_vars) == {"latitude", "longitude", "level", "date", "value"}
    assert x["value"].shape == (8,)
    xr.testing.assert_identical(x, ds.to_xarray())

    x = fl[1:].to_xarray()
    assert x["value"].shape == (4,)


def test_geopoints_featurelist_to_data_object():
    import xarray as xr

    fl = _featurelist("geopointset.gpts")
    d = fl.to_data_object()
    assert isinstance(d, FeatureListData)
    assert d.available_types == ["featurelist", "xarray"]
    assert d.to_featurelist() is fl
    assert isinstance(d.to_xarray(), xr.Dataset)
    assert d.to_xarray()["value"].shape == (8,)

    d = fl[1:].to_data_object()
    assert len(d.to_featurelist()) == 2


def test_geopoints_featurelist_from_data_object_round_trip():
    ds = from_source("file", _data_file("geopointset.gpts"))
    fl = ds.to_featurelist()
    d = fl.sel(param="geopotential").to_data_object()
    assert len(d.to_featurelist()) == 1


def test_geopoints_featurelist_repr():
    fl = _featurelist("geopointset.gpts")
    assert repr(fl) == "GeopointsFeatureList(len=3)"
    assert repr(fl[1:]) == "GeopointsFeatureList(len=2)"


def test_geopoints_featurelist_from_plain_list():
    fl = _featurelist("geopointset.gpts")
    fl2 = GeopointsFeatureList([fl[2], fl[0]])
    assert [len(f) for f in fl2] == [3, 4]
    assert len(GeopointsFeatureList()) == 0
    assert len(GeopointsFeatureList(None)) == 0


# -- row mode ---------------------------------------------------------------------------------

ROW_COLUMNS = ["latitude", "longitude", "level", "date", "value"]


def _rows(name):
    return _featurelist(name, mode="row")


def _is_plain(v):
    return v is None or type(v) in (int, float, str, pd.Timestamp, type(pd.NaT))


@pytest.mark.parametrize("name", GEOPOINTS_FILES)
def test_geopoints_row_featurelist_all_files(name):
    ds = from_source("file", _data_file(name))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()
    assert isinstance(fl, GeopointsRowFeatureList)
    assert len(fl) == len(df)
    features = list(fl)
    assert len(features) == len(df)
    assert all(isinstance(f, GeopointsRowFeature) for f in features)
    pd.testing.assert_frame_equal(fl.to_pandas(), df)

    # the features are in file order
    for i in (0, len(df) - 1):
        m = fl[i].metadata()
        for col in df.columns:
            expected = df.loc[i, col]
            assert m[col] == expected or (pd.isna(m[col]) and pd.isna(expected))
    assert all(_is_plain(v) for f in features for v in f.metadata().values())


def test_geopoints_row_featurelist_mode_via_reader_and_helper():
    ds = from_source("file", _data_file("geopointset.gpts"))
    assert len(ds._reader.to_featurelist(mode="row")) == 8
    assert len(make_featurelist(ds._reader.blocks, "row")) == 8
    assert len(make_featurelist(ds._reader.blocks, mode="block")) == 3
    assert len(make_featurelist([], "row")) == 0
    # blocks of any origin, e.g. from several files
    blocks = from_source("file", _data_file("traditional.gpt"))._reader.blocks + ds._reader.blocks
    fl = make_featurelist(blocks, "row")
    assert len(fl) == 16
    assert fl[8].metadata("latitude") == 69.6523
    assert fl[-1].metadata("latitude") == 53.71


def test_geopoints_row_featurelist_empty_set(tmp_path):
    ds = from_source("file", _write(tmp_path, "#GEOPOINTSET\n", "empty.gpts"))
    fl = ds.to_featurelist(mode="row")
    assert isinstance(fl, GeopointsRowFeatureList)
    assert len(fl) == 0
    assert list(fl) == []
    assert fl.metadata("param", default=None) == []
    assert fl.to_pandas().empty
    assert len(fl.to_xarray().data_vars) == 0
    assert len(fl.sel(param="a")) == 0
    assert len(fl.order_by("param")) == 0
    assert len(fl[:]) == 0
    assert len(fl.ls()) == 0
    assert len(fl.head()) == 0
    assert len(fl.tail()) == 0
    assert repr(fl) == "GeopointsRowFeatureList(len=0)"
    with pytest.raises(IndexError):
        fl[0]
    with pytest.raises(IndexError):
        fl[-1]


def test_geopoints_row_featurelist_block_without_rows(tmp_path):
    fl = from_source("file", _write(tmp_path, "#GEO\n#METADATA\nparam=t\n#DATA\n")).to_featurelist(mode="row")
    assert len(fl) == 0
    assert list(fl) == []
    assert len(fl.to_pandas()) == 0
    assert len(fl.ls()) == 0


def test_geopoints_row_featurelist_set_with_empty_blocks(tmp_path):
    text = (
        "#GEOPOINTSET\n"
        "#GEO\n#METADATA\nparam=a\n#DATA\n"
        "#GEO\n#METADATA\nparam=b\n#DATA\n1 2 0 20130512 0 3.0\n2 3 0 20130512 0 4.0\n"
        "#GEO\n#DATA\n"
        "#GEO\n#METADATA\nparam=d\n#DATA\n5 6 0 20130512 0 7.0\n"
        "#GEO\n#DATA\n"
    )
    ds = from_source("file", _write(tmp_path, text, "nodata.gpts"))
    fl = ds.to_featurelist(mode="row")
    assert len(ds.to_featurelist()) == 5
    assert len(fl) == 3 == len(ds.to_pandas())
    assert fl.metadata("param") == ["b", "b", "d"]
    assert fl.metadata("value") == [3.0, 4.0, 7.0]
    assert [f.metadata("latitude") for f in fl[1:]] == [2.0, 5.0]
    assert fl[-1].metadata("param") == "d"
    pd.testing.assert_frame_equal(fl.to_pandas(), ds.to_pandas())
    pd.testing.assert_frame_equal(fl[1:].to_pandas(), ds.to_pandas().iloc[1:].reset_index(drop=True))


def test_geopoints_row_featurelist_laziness(monkeypatch):
    ds = from_source("file", _data_file("traditional.gpt"))

    def fail(*args, **kwargs):
        raise AssertionError("a row feature has been created")

    monkeypatch.setattr(GeopointsRowFeature, "__init__", fail)
    fl = ds.to_featurelist(mode="row")
    assert len(fl) == 8
    assert len(fl[2:6]) == 4
    assert len(fl[::-1]) == 8
    assert len(fl.to_pandas()) == 8
    assert len(fl[2:].to_pandas()) == 6
    with pytest.raises(AssertionError):
        fl[0]


# -- row feature --------------------------------------------------------------------------------


def test_geopoints_row_metadata_header_and_columns():
    ds = from_source("file", _data_file("metadata.gpt"))
    fl = ds.to_featurelist(mode="row")
    assert len(fl) == len(ds.to_pandas()) == 44

    f = fl[0]
    assert isinstance(f, GeopointsRowFeature)
    m = f.metadata()
    assert m == {
        "param": "temperature",
        "date": pd.Timestamp("2013-08-04 12:00"),
        "time": 1200,
        "level": 0.2,
        "latitude": 55.01,
        "longitude": 8.41,
        "value": 294.4,
    }
    # the header keys first, then the other columns; the row value wins for "date" and "level"
    assert list(m) == ["param", "date", "time", "level", "latitude", "longitude", "value"]
    assert type(m["date"]) is pd.Timestamp
    assert type(m["time"]) is int
    assert type(m["latitude"]) is float
    assert type(m["level"]) is float
    assert fl[43].metadata("latitude", "longitude", "value") == [47.88, 8.0, 290.5]
    assert fl[-1].metadata("date") == pd.Timestamp("2013-08-04 12:00")

    # the block feature keeps the header only
    assert ds.to_featurelist()[0].metadata("date") == 20130804


def test_geopoints_row_metadata_row_value_wins(tmp_path):
    text = "#GEO\n#METADATA\nvalue=header\nlevel=5\nparam=p\n#DATA\n1 2 7 20130512 600 3.5\n"
    f = from_source("file", _write(tmp_path, text)).to_featurelist(mode="row")[0]
    assert f.metadata("value") == 3.5
    assert f.metadata("level") == 7.0
    assert f.metadata("param") == "p"
    assert list(f.metadata()) == ["value", "level", "param", "latitude", "longitude", "date"]


def test_geopoints_row_metadata_ncols_stnid():
    fl = _rows("ncols_stnid.gpt")
    assert len(fl) == 4
    assert fl.metadata("stnid") == ["heathrow", "oxford", "texas", "aberdeen"]
    assert fl[1].metadata() == {
        "stnid": "oxford",
        "latitude": 31.72,
        "longitude": 35.98,
        "level": 20.0,
        "date": pd.Timestamp("2012-02-18 18:00"),
        "_v1": 274.9,
        "_v2": 28.0,
        "_v3": 1.0,
    }

    r = fl.sel(stnid="oxford")
    assert isinstance(r, GeopointsRowFeatureList)
    assert len(r) == 1
    assert r[0].metadata("latitude") == 31.72
    assert len(fl.sel(stnid=["oxford", "texas"])) == 2
    assert fl.sel(stnid=["texas", "oxford"]).metadata("stnid") == ["oxford", "texas"]
    assert len(fl.sel(stnid="nothing")) == 0
    assert len(fl.sel(level=slice(15, 25))) == 1
    assert fl.sel(date=pd.Timestamp("2012-02-18 06:00")).metadata("stnid") == ["heathrow"]


def test_geopoints_row_metadata_stnid_none(tmp_path):
    def is_none(x):
        return x is None

    # no stnid column in the file: it is added with None
    fl = _rows("ncols.gpt")
    assert len(fl) == 4
    assert all(f.metadata("stnid") is None for f in fl)
    assert fl[0].metadata()["stnid"] is None
    assert list(fl[0].metadata())[:3] == ["stnid", "latitude", "longitude"]
    assert fl.ls(keys=["stnid"])["stnid"].tolist() == [None] * 4
    assert len(fl.sel(stnid=is_none)) == 4

    # "?" in the file is a missing stnid
    text = "#GEO\n#FORMAT NCOLS\n#COLUMNS\nstnid latitude longitude level date time\n#DATA\n"
    text += "a 1 2 0 20130512 0 5\n? 3 4 0 20130512 0 6\n"
    fl = from_source("file", _write(tmp_path, text)).to_featurelist(mode="row")
    assert fl.metadata("stnid") == ["a", None]
    assert fl.sel(stnid="a").metadata("latitude") == [1.0]
    r = fl.sel(stnid=is_none)
    assert r.metadata("latitude") == [3.0]
    assert r[0].metadata("stnid") is None
    assert r.to_pandas()["stnid"].tolist() == [None]
    # None is last
    assert fl[::-1].order_by("stnid").metadata("latitude") == [1.0, 3.0]
    assert fl[::-1].order_by(stnid="descending").metadata("latitude") == [1.0, 3.0]


def test_geopoints_row_metadata_missing_values():
    fl = _rows("missing_latlon.gpt")
    assert len(fl) == 7
    m = fl[1].metadata()
    assert m["latitude"] != m["latitude"]
    assert m["longitude"] == 8.8
    assert type(m["latitude"]) is float
    assert fl[3].metadata("longitude") != fl[3].metadata("longitude")
    assert fl[3].metadata("latitude") == 47.88
    m = fl[5].metadata()
    assert m["latitude"] != m["latitude"]
    assert m["longitude"] != m["longitude"]
    assert m["level"] == 49.0
    assert m["date"] == pd.Timestamp("2017-08-14 09:00")

    # the header keys are still there
    assert m["param"] == "temperature"
    assert m["time"] == 1200

    # missing values are found by the default
    assert fl.metadata("latitude", default=None)[1] != fl.metadata("latitude", default=None)[1]

    # and sorted last
    lats = fl.order_by("latitude").metadata("latitude")
    assert lats[:5] == [47.88, 50.87, 52.98, 53.06, 54.33]
    assert all(x != x for x in lats[5:])
    lats = fl.order_by(latitude="descending").metadata("latitude")
    assert lats[:5] == [54.33, 53.06, 52.98, 50.87, 47.88]
    assert all(x != x for x in lats[5:])


def test_geopoints_row_metadata_set():
    fl = _rows("geopointset.gpts")
    assert len(fl) == 8
    # the blocks without #METADATA only have the columns of the row
    for i in (0, 1, 2, 3, 5, 6, 7):
        assert list(fl[i].metadata()) == ROW_COLUMNS
        assert fl[i].metadata("param", default=None) is None
        assert fl[i].default_ls_keys == ROW_COLUMNS
        with pytest.raises(KeyError):
            fl[i].metadata("param")

    m = fl[4].metadata()
    assert list(m) == ["param"] + ROW_COLUMNS
    assert m["param"] == "geopotential"
    assert m["value"] == 101045.8
    assert m["date"] == pd.Timestamp("2013-05-12 06:00")

    assert fl.metadata("param", default=None) == [None] * 4 + ["geopotential"] + [None] * 3
    assert len(fl.sel(param="geopotential")) == 1
    assert fl[0].metadata("date") == pd.Timestamp("2013-05-12 00:00")
    assert fl[5].metadata("date") == pd.Timestamp("2013-05-13 00:00")


def test_geopoints_row_metadata_other_formats():
    f = _rows("xyv.gpt")[0]
    assert list(f.metadata()) == ["longitude", "latitude", "value"]
    assert f.format == "XYV"
    f = _rows("polar_vector.gpt")[0]
    assert list(f.metadata())[-2:] == ["magnitude", "angle"]
    f = _rows("xy_vector.gpt")[0]
    assert list(f.metadata())[-2:] == ["x-comp", "y-comp"]


def test_geopoints_row_text_values(tmp_path):
    text = "#GEO\n#DATA\n1 2 0 20130512 0 abc\n3 4 0 20130512 0 5.5\n"
    fl = from_source("file", _write(tmp_path, text)).to_featurelist(mode="row")
    assert fl.metadata("value") == ["abc", 5.5]
    assert type(fl[1].metadata("value")) is float
    assert len(fl.sel(value="abc")) == 1


def test_geopoints_row_time_column_without_date(tmp_path):
    text = "#GEO\n#FORMAT NCOLS\n#COLUMNS\nlatitude longitude time v\n#DATA\n1 2 1230 5\n"
    f = from_source("file", _write(tmp_path, text)).to_featurelist(mode="row")[0]
    m = f.metadata()
    assert m["time"] == 1230
    assert type(m["time"]) is int


def test_geopoints_row_missing_date(tmp_path):
    text = "#GEO\n#DATA\n1 2 0 3e38 0 5\n"
    f = from_source("file", _write(tmp_path, text)).to_featurelist(mode="row")[0]
    assert f.metadata("date") is pd.NaT


def test_geopoints_row_feature_metadata_forms():
    f = _rows("metadata.gpt")[0]
    assert f.metadata("param") == "temperature"
    assert f.metadata("latitude") == 55.01
    assert f.metadata(["param", "latitude"]) == ["temperature", 55.01]
    assert f.metadata("param", "latitude") == ["temperature", 55.01]
    assert f.metadata(("param", "latitude")) == ["temperature", 55.01]
    assert f.metadata("param", ["latitude", "value"]) == ["temperature", 55.01, 294.4]
    assert f.metadata([]) == []
    with pytest.raises(KeyError, match="foo"):
        f.metadata("foo")
    with pytest.raises(KeyError, match="foo"):
        f.metadata(["param", "foo"])
    assert f.metadata("foo", default=None) is None
    assert f.metadata(["foo", "latitude"], default=0) == [0, 55.01]
    assert f.metadata("latitude", default=7) == 55.01
    assert f.metadata("latitude", astype=int) == 55
    assert f.metadata(["latitude", "param"], astype=[str, str]) == ["55.01", "temperature"]
    with pytest.raises(ValueError):
        f.metadata(1)


def test_geopoints_row_feature_metadata_is_copy():
    f = _rows("metadata.gpt")[0]
    m = f.metadata()
    m["param"] = "changed"
    m["latitude"] = -1
    assert f.metadata("param") == "temperature"
    assert f.metadata("latitude") == 55.01


def test_geopoints_row_feature_internal_access():
    f = _rows("metadata.gpt")[1]
    assert f._default_encoder() is None
    assert f.default_ls_keys == ["param", "date", "time", "level", "latitude", "longitude", "value"]
    assert f.format == "TRADITIONAL"
    assert f.row == 1

    assert f._get_single("latitude") == 54.33
    assert f._get_single("param") == "temperature"
    assert f._get_single("foo") is None
    assert f._get_single("foo", default=3) == 3
    assert f._get_single("latitude", astype=str) == "54.33"
    with pytest.raises(KeyError):
        f._get_single("foo", raise_on_missing=True)

    assert f._get_fast("latitude") == 54.33
    assert f._get_fast("latitude", output=dict) == {"latitude": 54.33}
    assert f._get_fast(["latitude", "foo"], default=[None, None], astype=[None, None]) == [54.33, None]
    assert f._get_fast(("param", "latitude"), output=tuple) == ("temperature", 54.33)
    assert f._get_fast(
        keys=["param", "foo"],
        default=[None, 1],
        astype=[None, None],
        collections=None,
        output=dict,
        flatten_dict=True,
    ) == {"param": "temperature", "foo": 1}
    with pytest.raises(KeyError):
        f._get_fast(["latitude", "foo"], raise_on_missing=True)


def test_geopoints_row_feature_repr():
    f = _rows("xyv.gpt")[1]
    r = repr(f)
    assert r.startswith("GeopointsRowFeature(format='XYV', row=1, metadata={'longitude': ")


def test_geopoints_row_feature_direct():
    ds = from_source("file", _data_file("metadata.gpt"))
    block = ds._reader.blocks[0]
    f = GeopointsRowFeature(block, 3)
    assert f.row == 3
    assert f.metadata("latitude") == ds.to_pandas().loc[3, "latitude"]
    assert f.metadata("param") == "temperature"
    assert GeopointsRowFeature(block, -1).row == 43
    with pytest.raises(IndexError):
        GeopointsRowFeature(block, 44)
    with pytest.raises(IndexError):
        GeopointsRowFeature(block, -45)


def test_geopoints_row_feature_to_pandas():
    ds = from_source("file", _data_file("metadata.gpt"))
    df = ds.to_pandas()
    f = ds.to_featurelist(mode="row")[2]
    r = f.to_pandas()
    assert isinstance(r, pd.DataFrame)
    assert r.shape == (1, len(df.columns))
    assert list(r.columns) == list(df.columns)
    assert r.dtypes.equals(df.dtypes)
    assert list(r.index) == [0]
    pd.testing.assert_frame_equal(r, df.iloc[[2]].reset_index(drop=True))

    # a copy
    r.loc[0, "value"] = -1.0
    assert f.to_pandas().loc[0, "value"] == df.loc[2, "value"]
    assert ds.to_pandas().loc[2, "value"] == df.loc[2, "value"]


def test_geopoints_row_feature_to_pandas_dtypes():
    ds = from_source("file", _data_file("ncols_stnid.gpt"))
    df = ds.to_pandas()
    for i, f in enumerate(ds.to_featurelist(mode="row")):
        r = f.to_pandas()
        assert r.dtypes.equals(df.dtypes)
        pd.testing.assert_frame_equal(r, df.iloc[[i]].reset_index(drop=True))

    ds = from_source("file", _data_file("ncols.gpt"))
    r = ds.to_featurelist(mode="row")[0].to_pandas()
    assert r.dtypes.equals(ds.to_pandas().dtypes)
    assert r["stnid"].tolist() == [None]


def test_geopoints_row_feature_to_xarray():
    import xarray as xr

    f = _rows("traditional.gpt")[3]
    x = f.to_xarray()
    assert isinstance(x, xr.Dataset)
    assert set(x.data_vars) == set(ROW_COLUMNS)
    assert x["value"].shape == (1,)
    assert float(x["value"][0]) == 294.8


def test_geopoints_row_feature_pickle():
    f = _rows("geopointset.gpts")[4]
    f2 = pickle.loads(pickle.dumps(f))
    assert f2.metadata() == f.metadata()
    pd.testing.assert_frame_equal(f2.to_pandas(), f.to_pandas())


# -- row list: indexing, slicing, iteration -------------------------------------------------------


def test_geopoints_row_featurelist_indexing():
    ds = from_source("file", _data_file("geopointset.gpts"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()
    for i in range(8):
        assert fl[i].metadata("value") == df.loc[i, "value"]
        assert fl[i].row == [0, 1, 2, 3, 0, 0, 1, 2][i]
    assert fl[-1].metadata("value") == df.loc[7, "value"]
    assert fl[-8].metadata("value") == df.loc[0, "value"]

    with pytest.raises(IndexError):
        fl[8]
    with pytest.raises(IndexError):
        fl[-9]
    with pytest.raises(TypeError):
        fl["a"]

    import numpy as np

    assert fl[np.int64(2)].metadata("value") == df.loc[2, "value"]
    assert fl[np.int64(-1)].metadata("value") == df.loc[7, "value"]


def test_geopoints_row_featurelist_iteration():
    ds = from_source("file", _data_file("geopointset.gpts"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()
    assert [f.metadata("value") for f in fl] == df["value"].tolist()
    assert [f.metadata("value") for f in fl[::-1]] == df["value"].tolist()[::-1]
    assert [f.metadata("value") for f in fl[5:]] == df["value"].tolist()[5:]
    assert len(list(fl)) == len(list(fl)) == 8


def test_geopoints_row_featurelist_slicing():
    ds = from_source("file", _data_file("geopointset.gpts"))
    fl = ds.to_featurelist(mode="row")
    values = ds.to_pandas()["value"].tolist()

    s = fl[2:6]
    assert isinstance(s, GeopointsRowFeatureList)
    assert len(s) == 4
    assert s.metadata("value") == values[2:6]
    assert s[0].metadata("value") == values[2]
    assert s[-1].metadata("value") == values[5]

    assert fl[::2].metadata("value") == values[::2]
    assert fl[::-1].metadata("value") == values[::-1]
    assert fl[-3:].metadata("value") == values[-3:]
    assert len(fl[20:]) == 0
    assert len(fl[:]) == 8
    assert fl[:].metadata("value") == values
    assert fl[[0, 7, -1]].metadata("value") == [values[0], values[7], values[7]]

    import numpy as np

    assert fl[np.array([1, 3])].metadata("value") == [values[1], values[3]]

    with pytest.raises(IndexError):
        fl[[8]]
    with pytest.raises(IndexError):
        fl[[-9]]


def test_geopoints_row_featurelist_slice_of_slice():
    ds = from_source("file", _data_file("geopointset.gpts"))
    fl = ds.to_featurelist(mode="row")
    values = ds.to_pandas()["value"].tolist()

    s = fl[1:7][1:4]
    assert isinstance(s, GeopointsRowFeatureList)
    assert s.metadata("value") == values[2:5]

    s = fl[::-1][:3]
    assert s.metadata("value") == values[::-1][:3]
    assert s[-1].metadata("value") == values[5]

    s = fl[::2][::-1][1:]
    assert s.metadata("value") == values[::2][::-1][1:]

    assert len(fl[2:4][5:]) == 0
    with pytest.raises(IndexError):
        fl[2:4][2]
    with pytest.raises(IndexError):
        fl[2:4][-3]


def test_geopoints_row_featurelist_sequence_indices_must_be_integers():
    import numpy as np

    fl = _rows("geopointset.gpts")
    sel = fl.sel(latitude=slice(60, 64))
    assert len(sel) > 2

    bad = [
        [1.9],
        [1.0],
        ["2"],
        [None],
        [0, 1.5],
        [[0]],
        (1.9,),
        ("2",),
        np.array([1.5]),
        np.array([1.0]),
        np.array(["2"]),
        np.array([1, 2], dtype=float),
        [np.float64(1)],
        [np.True_],
        np.array([[0, 1]]),
        np.array(1),
        np.array([1, 1.5], dtype=object),
    ]
    # the same on the full list, a slice, a selection and a slice of a selection
    for lst in [fl, fl[1:], fl[::-1], sel, sel[1:], fl[2:][1:]]:
        for idx in bad:
            with pytest.raises(TypeError):
                lst[idx]

    # the scalar is rejected as well
    with pytest.raises(TypeError):
        fl[1.9]

    # the examples of the report
    with pytest.raises(TypeError):
        fl[1:][[0.5]]
    with pytest.raises(TypeError):
        fl.sel(latitude=slice(60, 64))[[1.2]]


def test_geopoints_row_featurelist_sequence_indices_valid():
    import numpy as np

    fl = _rows("geopointset.gpts")
    values = fl.metadata("value")

    def vals(lst):
        return lst.metadata("value")

    # list, tuple, numpy integer arrays (any int dtype), negative and repeated positions
    assert vals(fl[[1, 3]]) == [values[1], values[3]]
    assert vals(fl[(1, 3)]) == [values[1], values[3]]
    assert vals(fl[[0, 7, -1, -8, 7, 7]]) == [values[i] for i in [0, 7, 7, 0, 7, 7]]
    for dtype in [np.int8, np.int32, np.int64, np.uint8, np.uint64]:
        assert vals(fl[np.array([2, 0, 2], dtype=dtype)]) == [values[i] for i in [2, 0, 2]]
    assert vals(fl[np.array([-1, -2])]) == [values[7], values[6]]
    assert vals(fl[[np.int64(1), np.int8(-1), True]]) == [values[1], values[7], values[1]]
    assert vals(fl[np.array([1, 2], dtype=object)]) == [values[1], values[2]]

    # empty sequences
    assert len(fl[[]]) == 0
    assert len(fl[()]) == 0
    assert len(fl[np.array([], dtype=np.int64)]) == 0
    assert len(fl[np.array([])]) == 0

    # chained
    assert vals(fl[1:][[0, -1]]) == [values[1], values[7]]
    assert vals(fl[[5, 1, 3]][np.array([2, 0, 0])]) == [values[3], values[5], values[5]]
    assert vals(fl[::-1][[0, 1]]) == [values[7], values[6]]
    sel = fl.sel(latitude=slice(60, 64))
    sel_values = vals(sel)
    assert vals(sel[[1, 0, -1]]) == [sel_values[1], sel_values[0], sel_values[-1]]
    assert vals(sel[[0, 1, 2]][1:]) == sel_values[1:3]

    # still out of range
    for idx in [[8], [-9], np.array([8]), np.array([0, -9]), np.array([2**63], dtype=np.uint64), [2**70]]:
        with pytest.raises(IndexError):
            fl[idx]
    with pytest.raises(IndexError):
        fl[1:3][[2]]
    with pytest.raises(IndexError):
        sel[[len(sel)]]


def test_geopoints_row_featurelist_sequence_indices_bool_as_block_mode():
    import numpy as np

    # The framework treats a boolean array (or list) like a sequence of the positions 0 and 1, it
    # is not a mask. The block list does the same, so both list kinds give the same result.
    ds = from_source("file", _data_file("geopointset.gpts"))
    blocks = ds.to_featurelist()
    rows = ds.to_featurelist(mode="row")
    # a list with 3 blocks and one with 8 rows
    mask = np.array([True, False, True])
    r = blocks[mask]
    assert [len(f) for f in r] == [len(blocks[i]) for i in [1, 0, 1]]

    values = rows.metadata("value")
    for m in [mask, mask.tolist(), tuple(mask.tolist()), np.array([True] * 5 + [False] * 3)]:
        expected = [values[int(i)] for i in np.asarray(m)]
        assert rows[m].metadata("value") == expected
    # same positions as the block list for the same input
    assert [len(f) for f in blocks[mask.tolist()]] == [len(f) for f in blocks[mask]]
    assert rows[mask].to_pandas()["value"].tolist() == [values[1], values[0], values[1]]
    assert len(rows[np.array([], dtype=bool)]) == 0
    # chained
    assert rows[2:][mask].metadata("value") == [values[3], values[2], values[3]]


def test_geopoints_row_featurelist_pickle():
    fl = _rows("geopointset.gpts")
    fl2 = pickle.loads(pickle.dumps(fl))
    assert isinstance(fl2, GeopointsRowFeatureList)
    assert len(fl2) == 8
    assert fl2.metadata("value") == fl.metadata("value")
    pd.testing.assert_frame_equal(fl2.to_pandas(), fl.to_pandas())

    s = fl[::-1][1:5]
    s2 = pickle.loads(pickle.dumps(s))
    assert s2.metadata("value") == s.metadata("value")
    pd.testing.assert_frame_equal(s2.to_pandas(), s.to_pandas())


def test_geopoints_row_featurelist_repr():
    fl = _rows("geopointset.gpts")
    assert repr(fl) == "GeopointsRowFeatureList(len=8)"
    assert repr(fl[2:]) == "GeopointsRowFeatureList(len=6)"


# -- row list: sel and order_by ---------------------------------------------------------------


def test_geopoints_row_featurelist_sel():
    ds = from_source("file", _data_file("metadata.gpt"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()

    r = fl.sel(latitude=54.33)
    assert isinstance(r, GeopointsRowFeatureList)
    mask = df["latitude"] == 54.33
    assert len(r) == int(mask.sum()) > 0
    assert r.metadata("value") == df.loc[mask, "value"].tolist()

    # header key: all rows match
    assert len(fl.sel(param="temperature")) == 44
    assert len(fl.sel(param="other")) == 0
    # the row value wins for "date"
    assert len(fl.sel(date=pd.Timestamp("2013-08-04 12:00"))) == 44
    assert len(fl.sel(date=20130804)) == 0
    # the header key that is not a column
    assert len(fl.sel(time=1200)) == 44

    r = fl.sel(latitude=slice(50, 55), param="temperature")
    mask = (df["latitude"] >= 50) & (df["latitude"] <= 55)
    assert len(r) == int(mask.sum())
    assert r.metadata("latitude") == df.loc[mask, "latitude"].tolist()


def test_geopoints_row_featurelist_sel_to_pandas():
    ds = from_source("file", _data_file("metadata.gpt"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()

    r = fl.sel(latitude=slice(50, 55))
    mask = (df["latitude"] >= 50) & (df["latitude"] <= 55)
    out = r.to_pandas()
    pd.testing.assert_frame_equal(out, df[mask].reset_index(drop=True))
    assert list(out.index) == list(range(len(out)))

    assert fl.sel(latitude=1000).to_pandas().empty

    # a single row
    r = fl.sel(latitude=54.33)
    pd.testing.assert_frame_equal(r.to_pandas(), df[df["latitude"] == 54.33].reset_index(drop=True))


def test_geopoints_row_featurelist_sel_on_slice():
    ds = from_source("file", _data_file("traditional.gpt"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()

    s = fl[2:]
    r = s.sel(latitude=slice(40, 46))
    assert isinstance(r, GeopointsRowFeatureList)
    sub = df.iloc[2:]
    expected = sub[(sub["latitude"] >= 40) & (sub["latitude"] <= 46)]
    assert r.metadata("latitude") == expected["latitude"].tolist()
    pd.testing.assert_frame_equal(r.to_pandas(), expected.reset_index(drop=True))

    # not in the slice
    assert len(fl[2:].sel(latitude=36.15)) == 0
    assert len(fl.sel(latitude=36.15)) == 1
    # a slice and then a sel on the reversed slice
    r = fl[::-1].sel(latitude=slice(40, 46))
    assert r.metadata("latitude") == [x for x in df["latitude"].tolist()[::-1] if 40 <= x <= 46]


def test_geopoints_row_featurelist_slice_of_sel():
    ds = from_source("file", _data_file("traditional.gpt"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()

    sel = fl.sel(latitude=slice(36, 46))
    expected = df[(df["latitude"] >= 36) & (df["latitude"] <= 46)].reset_index(drop=True)
    assert len(expected) > 3

    s = sel[1:3]
    assert isinstance(s, GeopointsRowFeatureList)
    assert s.metadata("latitude") == expected["latitude"].tolist()[1:3]
    pd.testing.assert_frame_equal(s.to_pandas(), expected.iloc[1:3].reset_index(drop=True))
    assert sel[-1].metadata("latitude") == expected["latitude"].tolist()[-1]
    assert sel[::-1][0].metadata("latitude") == expected["latitude"].tolist()[-1]
    assert sel[1:][1:].metadata("latitude") == expected["latitude"].tolist()[2:]
    assert len(sel[len(sel) :]) == 0
    with pytest.raises(IndexError):
        sel[len(sel)]

    # and sel of a slice of a sel
    r = sel[1:].sel(latitude=slice(40, 46))
    assert r.metadata("latitude") == [x for x in expected["latitude"].tolist()[1:] if 40 <= x <= 46]


def test_geopoints_row_featurelist_order_by_missing_last():
    ds = from_source("file", _data_file("traditional.gpt"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()
    assert df["value"].isna().sum() == 1

    r = fl.order_by("value")
    assert isinstance(r, GeopointsRowFeatureList)
    assert len(r) == 8
    values = r.metadata("value")
    assert values[:7] == sorted(v for v in df["value"].tolist() if v == v)
    assert values[7] != values[7]

    r = fl.order_by(value="descending")
    values = r.metadata("value")
    assert values[:7] == sorted((v for v in df["value"].tolist() if v == v), reverse=True)
    assert values[7] != values[7]

    # to_pandas follows the order of the list
    r = fl.order_by("value")
    expected = df.sort_values("value", kind="stable", na_position="last").reset_index(drop=True)
    pd.testing.assert_frame_equal(r.to_pandas(), expected)
    r = fl.order_by(value="descending")
    expected = df.sort_values("value", ascending=False, kind="stable", na_position="last").reset_index(drop=True)
    pd.testing.assert_frame_equal(r.to_pandas(), expected)


def test_geopoints_row_featurelist_order_by_chain_and_keys():
    ds = from_source("file", _data_file("traditional.gpt"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()

    r = fl.order_by("value")[:3]
    assert isinstance(r, GeopointsRowFeatureList)
    assert r.metadata("value") == sorted(df["value"].dropna().tolist())[:3]
    r = fl[::-1].order_by("value")[-2:]
    assert r.metadata("value")[0] == 301.6
    assert r.metadata("value")[1] != r.metadata("value")[1]

    r = fl.order_by("value").sel(latitude=slice(40, 46))
    expected = df[(df["latitude"] >= 40) & (df["latitude"] <= 46)].sort_values("value", na_position="last")
    assert r.metadata("latitude") == expected["latitude"].tolist()

    # several keys: level is the same for all rows, so value decides
    r = fl.order_by("level", value="descending")
    assert r.metadata("value")[:2] == [301.6, 300.9]
    assert fl.order_by() is fl


def test_geopoints_row_featurelist_order_by_on_set_with_header_keys():
    fl = _rows("geopointset.gpts")
    r = fl.order_by("param")
    # the row with a param first, the rows without it afterwards in file order
    assert r.metadata("param", default=None) == ["geopotential"] + [None] * 7
    assert r.metadata("value")[1:] == [v for i, v in enumerate(fl.metadata("value")) if i != 4]
    r = fl.order_by(param="descending")
    assert r.metadata("param", default=None)[0] == "geopotential"


# -- row list: to_pandas ---------------------------------------------------------------------------


def test_geopoints_row_featurelist_to_pandas_set():
    ds = from_source("file", _data_file("geopointset.gpts"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()

    pd.testing.assert_frame_equal(fl.to_pandas(), df)
    assert list(fl.to_pandas().index) == list(range(8))

    # it is a copy
    out = fl.to_pandas()
    out.loc[0, "value"] = -1.0
    assert fl.to_pandas().loc[0, "value"] == df.loc[0, "value"]
    assert ds.to_pandas().loc[0, "value"] == df.loc[0, "value"]

    # selections that cross the blocks
    for sl in (slice(2, 7), slice(None, None, -1), slice(3, 6), slice(None, None, 3)):
        pd.testing.assert_frame_equal(fl[sl].to_pandas(), df.iloc[sl].reset_index(drop=True))
    for idx in ([5, 0, 4, 1], [7, 7, 0], [4], [4, 4]):
        pd.testing.assert_frame_equal(fl[idx].to_pandas(), df.iloc[idx].reset_index(drop=True))

    pd.testing.assert_frame_equal(fl.sel(param="geopotential").to_pandas(), df.iloc[[4]].reset_index(drop=True))
    assert fl[:0].to_pandas().empty


def test_geopoints_row_featurelist_to_pandas_different_columns(tmp_path):
    text = """#GEOPOINTSET
#GEO
#METADATA
param=t
#DATA
10.0 20.0 0 20130512 0 1.5
11.0 21.0 0 20130512 0 2.5
#GEO
#FORMAT NCOLS
#COLUMNS
latitude longitude date t2
#DATA
12.0 22.0 20130513 280.5
13.0 23.0 20130513 281.5
"""
    ds = from_source("file", _write(tmp_path, text, "mixed.gpts"))
    fl = ds.to_featurelist(mode="row")
    df = ds.to_pandas()
    assert len(fl) == len(df) == 4
    pd.testing.assert_frame_equal(fl.to_pandas(), df)
    # the rows of one block only have the columns of the block
    assert "t2" not in fl[0].metadata()
    assert "t2" in fl[2].metadata()
    assert fl[2].metadata("t2") == 280.5
    assert list(fl[2].to_pandas().columns) == ["stnid", "latitude", "longitude", "date", "t2"]

    # a selection in the first block does not get the columns of the second
    out = fl[:2].to_pandas()
    assert list(out.columns) == ROW_COLUMNS
    pd.testing.assert_frame_equal(out, df.iloc[:2][ROW_COLUMNS].reset_index(drop=True))

    # across the blocks
    out = fl[1:3].to_pandas()
    pd.testing.assert_frame_equal(out, df.iloc[1:3].reset_index(drop=True))
    out = fl[[3, 0]].to_pandas()
    assert out["t2"].isna().tolist() == [False, True]
    assert fl[[3, 0]].metadata("latitude") == [13.0, 10.0]


def test_geopoints_row_featurelist_to_xarray():
    import xarray as xr

    ds = from_source("file", _data_file("geopointset.gpts"))
    fl = ds.to_featurelist(mode="row")
    x = fl.to_xarray()
    assert isinstance(x, xr.Dataset)
    xr.testing.assert_identical(x, ds.to_xarray())
    assert fl[2:5].to_xarray()["value"].shape == (3,)


def test_geopoints_row_featurelist_to_data_object():
    import xarray as xr

    fl = _rows("geopointset.gpts")
    d = fl.to_data_object()
    assert isinstance(d, FeatureListData)
    assert d.to_featurelist() is fl
    assert isinstance(d.to_xarray(), xr.Dataset)
    assert d.to_xarray()["value"].shape == (8,)


# -- row list: metadata, ls ---------------------------------------------------------------------


def test_geopoints_row_featurelist_metadata_and_get():
    fl = _rows("traditional.gpt")
    assert len(fl.metadata()) == 8
    assert fl.metadata()[0]["latitude"] == 36.15
    assert fl.metadata("latitude", "longitude")[1] == [34.58, 32.98]
    with pytest.raises(KeyError):
        fl.metadata("param")
    assert fl.metadata("param", default=None) == [None] * 8
    assert fl.get("latitude")[:2] == [36.15, 34.58]
    assert fl.get(["latitude", "param"], default=0)[0] == [36.15, 0]
    assert fl.get("latitude", output=dict)[0] == {"latitude": 36.15}
    assert fl[1:3].get("latitude") == [34.58, 41.97]


def test_geopoints_row_featurelist_ls():
    fl = _rows("metadata.gpt")
    df = fl.ls()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 44
    assert list(df.columns) == ["param", "date", "time", "level", "latitude", "longitude", "value"]
    assert df.iloc[0]["param"] == "temperature"
    assert df.iloc[0]["date"] == pd.Timestamp("2013-08-04 12:00")
    assert df.iloc[0]["time"] == 1200
    assert df.iloc[0]["latitude"] == 55.01

    df = fl.ls(n=3, keys=["latitude", "value"])
    assert list(df.columns) == ["latitude", "value"]
    assert len(df) == 3

    df = fl.head(2)
    assert len(df) == 2
    assert list(df.columns)[0] == "param"
    df = fl.tail(2)
    assert df["latitude"].tolist() == [fl[42].metadata("latitude"), 47.88]

    df = fl[3:6].ls()
    assert len(df) == 3
    assert df["latitude"].tolist() == [f.metadata("latitude") for f in fl[3:6]]

    df = fl.sel(latitude=54.33).ls(keys=["latitude"], extra_keys=["foo"])
    assert list(df.columns) == ["latitude", "foo"]
    assert df["foo"].tolist()[0] is None


def test_geopoints_row_featurelist_ls_set_union_of_keys():
    fl = _rows("geopointset.gpts")

    # the first row has no param, the fifth has
    df = fl.ls()
    assert len(df) == 8
    assert list(df.columns) == ROW_COLUMNS + ["param"]
    assert df["param"].tolist() == [None] * 4 + ["geopotential"] + [None] * 3

    # only the shown features count
    df = fl.head(3)
    assert list(df.columns) == ROW_COLUMNS
    assert list(fl.head(4).columns) == ROW_COLUMNS
    assert list(fl.head(5).columns) == ROW_COLUMNS + ["param"]
    assert "param" not in fl.tail(3).columns
    assert "param" in fl.tail(4).columns
    assert "param" not in fl[5:].ls().columns


def test_geopoints_row_featurelist_ls_mixed_columns(tmp_path):
    text = """#GEOPOINTSET
#GEO
#METADATA
param=t
#DATA
10.0 20.0 0 20130512 0 1.5
#GEO
#FORMAT NCOLS
#COLUMNS
latitude longitude date t2
#DATA
12.0 22.0 20130513 280.5
"""
    fl = from_source("file", _write(tmp_path, text, "mixed.gpts")).to_featurelist(mode="row")
    df = fl.ls()
    assert list(df.columns) == ["param", "latitude", "longitude", "level", "date", "value", "stnid", "t2"]
    assert pd.isna(df["t2"].tolist()[0])
    assert df["t2"].tolist()[1] == 280.5
    assert df["param"].tolist() == ["t", None]
    assert list(fl.head(1).columns) == ["param", "latitude", "longitude", "level", "date", "value"]


def test_geopoints_row_featurelist_from_several_files():
    a = from_source("file", _data_file("metadata.gpt"))._reader.blocks
    b = from_source("file", _data_file("geopointset.gpts"))._reader.blocks
    fl = make_featurelist(a + b, "row")
    assert len(fl) == 44 + 8
    expected = pd.concat([f.to_pandas() for f in make_featurelist(a + b, "block")], ignore_index=True)
    pd.testing.assert_frame_equal(fl.to_pandas(), expected)
    assert fl[44].metadata("value") == 100869.8625
    assert fl[43].metadata("param") == "temperature"
    assert fl[44].metadata("param", default=None) is None
    pd.testing.assert_frame_equal(fl[40:48].to_pandas(), expected.iloc[40:48].reset_index(drop=True))


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
