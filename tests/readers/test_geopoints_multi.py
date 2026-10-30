#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Several geopoints files given as one input give one GeopointsData."""

import shutil

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from earthkit.data import from_source
from earthkit.data.data.geopoints import GeopointsData
from earthkit.data.data.multi import MultiData
from earthkit.data.readers.geopoints.reader import (
    GeopointsReader,
    GeopointsReaderBase,
    MultiGeopointsReader,
)
from earthkit.data.sources.empty import EmptySource
from earthkit.data.utils.testing import earthkit_test_data_file


def _gp(name):
    return earthkit_test_data_file("geopoints", name)


def _single(name):
    return from_source("file", _gp(name))


def _stacked(*names):
    return pd.concat([_single(n).to_pandas() for n in names], ignore_index=True)


def _meta(fl):
    """The metadata of the features, with NaN replaced by a marker so that dicts compare equal."""
    return [{k: ("<nan>" if isinstance(v, float) and v != v else v) for k, v in f.metadata().items()} for f in fl]


def _check_multi(ds, names):
    """The common checks for the data of the files ``names``, in this order."""
    singles = [_single(n) for n in names]

    assert isinstance(ds, GeopointsData)
    assert ds._TYPE_NAME == "Geopoints"
    assert isinstance(ds.path, list)
    assert all(isinstance(p, str) for p in ds.path)
    assert [p.rsplit("/", 1)[-1] for p in ds.path] == list(names)
    assert ds.available_types == ["pandas", "xarray", "featurelist"]

    assert_frame_equal(ds.to_pandas(), _stacked(*names))

    ds_xr = ds.to_xarray()
    assert ds_xr.sizes["index"] == len(ds.to_pandas())

    fl = ds.to_featurelist()
    assert len(fl) == sum(len(s.to_featurelist()) for s in singles)
    assert _meta(fl) == [m for s in singles for m in _meta(s.to_featurelist())]
    assert [len(f) for f in fl] == [len(f) for s in singles for f in s.to_featurelist()]

    rl = ds.to_featurelist(mode="row")
    assert len(rl) == len(ds.to_pandas())
    assert _meta(rl) == [m for s in singles for m in _meta(s.to_featurelist(mode="row"))]
    assert_frame_equal(rl.to_pandas(), ds.to_pandas())
    assert_frame_equal(fl.to_pandas(), ds.to_pandas())

    with pytest.raises(ValueError):
        ds.to_featurelist(mode="bad")


# -- list of files ----------------------------------------------------------------------------


def test_geopoints_multi_list():
    names = ["metadata.gpt", "geopointset.gpts"]
    ds = from_source("file", [_gp(n) for n in names])
    _check_multi(ds, names)

    assert isinstance(ds._reader, MultiGeopointsReader)
    assert len(ds.path) == 2

    fl = ds.to_featurelist()
    assert len(fl) == 1 + 3
    assert fl[0].metadata() == {"param": "temperature", "date": 20130804, "time": 1200, "level": 0.2}
    # the first block of the set has no #METADATA
    assert fl[1].metadata() == {}
    assert _meta(fl)[1:] == _meta(_single("geopointset.gpts").to_featurelist())

    assert len(ds.to_featurelist(mode="row")) == len(_single("metadata.gpt").to_pandas()) + len(
        _single("geopointset.gpts").to_pandas()
    )


def test_geopoints_multi_list_reverse_order():
    names = ["geopointset.gpts", "metadata.gpt"]
    ds = from_source("file", [_gp(n) for n in names])
    _check_multi(ds, names)
    assert _meta(ds.to_featurelist())[-1]["param"] == "temperature"


def test_geopoints_multi_list_different_columns():
    names = ["traditional.gpt", "ncols_stnid.gpt"]
    ds = from_source("file", [_gp(n) for n in names])
    _check_multi(ds, names)

    df = ds.to_pandas()
    n1 = len(_single("traditional.gpt").to_pandas())
    n2 = len(_single("ncols_stnid.gpt").to_pandas())
    assert len(df) == n1 + n2
    assert "stnid" in df.columns
    # the columns missing in a file are NaN/None there
    assert df["stnid"].iloc[:n1].isna().all()
    assert not df["stnid"].iloc[n1:].isna().any()
    assert list(df.index) == list(range(n1 + n2))

    # rows of the second file carry their own columns
    rl = ds.to_featurelist(mode="row")
    assert rl[n1].metadata("stnid") == "heathrow"
    assert rl[0].metadata("stnid", default=None) is None


def test_geopoints_multi_list_many_files():
    names = ["metadata.gpt", "ncols.gpt", "geopointset.gpts", "xyv.gpt", "polar_vector.gpt"]
    ds = from_source("file", [_gp(n) for n in names])
    _check_multi(ds, names)


def test_geopoints_multi_list_with_empty_geopointset(tmp_path):
    empty = tmp_path / "empty.gpts"
    empty.write_text("#GEOPOINTSET\n")

    paths = [_gp("metadata.gpt"), str(empty), _gp("traditional.gpt")]
    ds = from_source("file", paths)
    assert isinstance(ds, GeopointsData)
    assert len(ds.path) == 3

    assert_frame_equal(ds.to_pandas(), _stacked("metadata.gpt", "traditional.gpt"))
    assert len(ds.to_featurelist()) == 2
    assert ds._reader.num_blocks == 2

    # only empty files
    ds = from_source("file", [str(empty), str(empty)])
    assert isinstance(ds, GeopointsData)
    assert ds.to_pandas().empty
    assert len(ds.to_featurelist()) == 0
    assert len(ds.to_featurelist(mode="row")) == 0


# -- glob and folder --------------------------------------------------------------------------


def test_geopoints_multi_glob():
    ds = from_source("file", _gp("*.gpt"))
    names = sorted([
        "metadata.gpt",
        "missing_latlon.gpt",
        "ncols.gpt",
        "ncols_stnid.gpt",
        "polar_vector.gpt",
        "traditional.gpt",
        "xy_vector.gpt",
        "xyv.gpt",
    ])
    _check_multi(ds, names)
    assert len(ds.to_featurelist()) == len(names)


def test_geopoints_multi_glob_with_set():
    ds = from_source("file", _gp("[gm]*.gpt*"))
    # geopointset.gpts, metadata.gpt, missing_latlon.gpt
    _check_multi(ds, ["geopointset.gpts", "metadata.gpt", "missing_latlon.gpt"])


def test_geopoints_multi_glob_single_match_is_single():
    ds = from_source("file", _gp("traditional.g*"))
    assert isinstance(ds, GeopointsData)
    assert isinstance(ds.path, str)
    assert isinstance(ds._reader, GeopointsReader)


def test_geopoints_multi_folder(tmp_path):
    names = ["geopointset.gpts", "metadata.gpt", "ncols_stnid.gpt"]
    for n in names:
        shutil.copy(_gp(n), tmp_path / n)

    ds = from_source("file", str(tmp_path))
    _check_multi(ds, names)
    assert len(ds.to_featurelist()) == 3 + 1 + 1


def test_geopoints_multi_folder_single_file(tmp_path):
    shutil.copy(_gp("metadata.gpt"), tmp_path / "metadata.gpt")

    ds = from_source("file", str(tmp_path))
    assert isinstance(ds, GeopointsData)
    assert isinstance(ds.path, str)
    assert len(ds.to_featurelist()) == 1


# -- the multi source -------------------------------------------------------------------------


def test_geopoints_multi_source():
    names = ["metadata.gpt", "traditional.gpt"]
    ds = from_source("multi", *[from_source("file", _gp(n)) for n in names])
    _check_multi(ds, names)


@pytest.mark.parametrize("merged_first", [True, False])
def test_geopoints_multi_source_merged_and_single(merged_first):
    merged_names = ["metadata.gpt", "geopointset.gpts"]
    merged = from_source("file", [_gp(n) for n in merged_names])
    assert isinstance(merged._reader, MultiGeopointsReader)
    single = _single("ncols_stnid.gpt")

    if merged_first:
        ds = from_source("multi", merged, single)
        names = merged_names + ["ncols_stnid.gpt"]
    else:
        ds = from_source("multi", single, merged)
        names = ["ncols_stnid.gpt"] + merged_names

    _check_multi(ds, names)
    assert isinstance(ds._reader, MultiGeopointsReader)
    # flattened: the readers of the files, not nested multi readers
    assert all(isinstance(s, GeopointsReader) for s in ds._reader.sources)
    assert len(ds._reader.sources) == 3
    assert ds.path == [_gp(n) for n in names]


def test_geopoints_multi_source_two_merged():
    a = from_source("file", [_gp("metadata.gpt"), _gp("ncols.gpt")])
    b = from_source("file", [_gp("geopointset.gpts"), _gp("xyv.gpt")])
    ds = from_source("multi", a, b)
    _check_multi(ds, ["metadata.gpt", "ncols.gpt", "geopointset.gpts", "xyv.gpt"])

    ds = from_source("multi", b, a)
    _check_multi(ds, ["geopointset.gpts", "xyv.gpt", "metadata.gpt", "ncols.gpt"])


def test_geopoints_multi_source_merged_nested_three_times():
    a = from_source("multi", _single("metadata.gpt"), _single("ncols.gpt"))
    b = from_source("multi", a, _single("xyv.gpt"))
    c = from_source("multi", _single("traditional.gpt"), b)
    _check_multi(c, ["traditional.gpt", "metadata.gpt", "ncols.gpt", "xyv.gpt"])


def test_geopoints_multi_source_does_not_change_inputs():
    merged = from_source("file", [_gp("metadata.gpt"), _gp("geopointset.gpts")])
    single = _single("traditional.gpt")
    from_source("multi", merged, single)

    assert isinstance(merged._reader, MultiGeopointsReader)
    assert len(merged._reader.sources) == 2
    assert isinstance(single._reader, GeopointsReader)
    assert isinstance(single.path, str)


# -- merge ------------------------------------------------------------------------------------


def test_geopoints_reader_class_hierarchy():
    assert issubclass(GeopointsReader, GeopointsReaderBase)
    assert issubclass(MultiGeopointsReader, GeopointsReaderBase)
    assert not issubclass(MultiGeopointsReader, GeopointsReader)


def test_geopoints_reader_single_is_its_own_source():
    ds = _single("metadata.gpt")
    assert ds._source is ds._reader
    assert ds._reader.mutate_source() is ds._reader
    assert ds._reader.is_multi is False
    assert ds._reader.num_files == 1


def test_geopoints_reader_merge():
    r1 = _single("metadata.gpt")._reader
    r2 = _single("geopointset.gpts")._reader
    r3 = _single("traditional.gpt")._reader

    m = GeopointsReader.merge([r1, r2])
    assert isinstance(m, MultiGeopointsReader)
    assert m.sources == [r1, r2]
    assert m.is_multi is True
    assert m.num_files == 2
    assert m.mutate() is m
    assert m.num_blocks == 4
    assert m.formats == ["TRADITIONAL"]

    # in any order and nesting
    assert GeopointsReaderBase.merge([r3, m]).sources == [r3, r1, r2]
    assert GeopointsReaderBase.merge([m, r3]).sources == [r1, r2, r3]
    assert GeopointsReaderBase.merge([m, m]).sources == [r1, r2, r1, r2]
    assert MultiGeopointsReader.merge([m, r3]).sources == [r1, r2, r3]

    # the input is not modified
    assert m.sources == [r1, r2]


def test_geopoints_reader_merge_ignores_ignored_sources():
    r1 = _single("metadata.gpt")._reader
    r2 = _single("traditional.gpt")._reader

    m = GeopointsReader.merge([r1, EmptySource(), r2])
    assert m.sources == [r1, r2]


def test_geopoints_reader_merge_errors():
    r1 = _single("metadata.gpt")._reader
    csv = from_source("file", earthkit_test_data_file("test.csv"))

    with pytest.raises(ValueError):
        GeopointsReader.merge([r1, csv._source])

    with pytest.raises(ValueError):
        GeopointsReader.merge([])

    with pytest.raises(ValueError):
        GeopointsReader.merge([EmptySource()])


# -- mixed inputs -----------------------------------------------------------------------------


@pytest.mark.parametrize("geo_first", [True, False])
def test_geopoints_multi_mixed_with_csv_is_multidata(geo_first):
    paths = [_gp("metadata.gpt"), earthkit_test_data_file("test.csv")]
    if not geo_first:
        paths.reverse()

    ds = from_source("file", paths)
    assert isinstance(ds, MultiData)
    assert ds._TYPE_NAME == "Multi"
    assert not isinstance(ds, GeopointsData)


def test_geopoints_multi_source_mixed_with_csv_is_multidata():
    ds = from_source("multi", _single("metadata.gpt"), from_source("file", earthkit_test_data_file("test.csv")))
    assert ds._TYPE_NAME == "Multi"


def test_geopoints_multi_source_mixed_with_merged_is_multidata():
    merged = from_source("file", [_gp("metadata.gpt"), _gp("traditional.gpt")])
    ds = from_source("multi", merged, from_source("file", earthkit_test_data_file("test.csv")))
    assert ds._TYPE_NAME == "Multi"


# -- describe and repr ------------------------------------------------------------------------


def test_geopoints_multi_title_and_repr():
    paths = [_gp("metadata.gpt"), _gp("geopointset.gpts")]
    ds = from_source("file", paths)

    assert ds._title() == "Geopoints files (2 files, 4 blocks, format: TRADITIONAL)"
    assert repr(ds) == f"GeopointsData(path={paths}, files=2, blocks=4, format=TRADITIONAL)"

    d = ds.describe()
    assert d.title == "Geopoints files (2 files, 4 blocks, format: TRADITIONAL)"
    assert d.path == paths
    assert "Geopoints files (2 files, 4 blocks" in ds._repr_html_()


def test_geopoints_multi_title_and_repr_several_formats():
    paths = [_gp("traditional.gpt"), _gp("ncols_stnid.gpt")]
    ds = from_source("file", paths)

    assert ds._title() == "Geopoints files (2 files, 2 blocks, format: TRADITIONAL, NCOLS)"
    assert repr(ds) == f"GeopointsData(path={paths}, files=2, blocks=2, format=TRADITIONAL,NCOLS)"


def test_geopoints_multi_title_and_repr_without_blocks(tmp_path):
    empty = tmp_path / "empty.gpts"
    empty.write_text("#GEOPOINTSET\n")

    ds = from_source("file", [str(empty), str(empty)])
    assert ds._title() == "Geopoints files (2 files, 0 blocks)"
    assert repr(ds) == f"GeopointsData(path={[str(empty), str(empty)]}, files=2, blocks=0)"


def test_geopoints_single_title_and_repr_unchanged():
    path = _gp("metadata.gpt")
    ds = from_source("file", path)
    assert ds._title() == "Geopoints file (format: TRADITIONAL)"
    assert repr(ds) == f"GeopointsData(path={path}, blocks=1, format=TRADITIONAL)"
    assert ds.path == path
    assert ds.describe().title == "Geopoints file (format: TRADITIONAL)"

    path = _gp("geopointset.gpts")
    ds = from_source("file", path)
    assert ds._title() == "Geopointset file (3 blocks, format: TRADITIONAL)"
    assert repr(ds) == f"GeopointsData(path={path}, blocks=3, format=TRADITIONAL)"
