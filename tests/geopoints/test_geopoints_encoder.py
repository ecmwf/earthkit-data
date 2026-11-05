#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Tests for the geopoints encoder.

A file read by the geopoints reader is copied to a file target as it is, everything else is
written back block by block: the features of a geopoints featurelist, the fields of a fieldlist
and the points of a GRIB field.
"""

import os

import numpy as np
import pytest
from pandas.testing import assert_frame_equal

from earthkit.data import create_encoder, from_source, to_target
from earthkit.data.readers.geopoints.reader import GeopointsReader
from earthkit.data.utils.testing import (
    earthkit_examples_file,
    earthkit_remote_test_data_file,
    earthkit_test_data_file,
)

GEOPOINTS_FILES = sorted(os.listdir(earthkit_test_data_file("geopoints")))

# a geopointset: 3 TRADITIONAL blocks with 4, 1 and 3 rows, the middle one has a #METADATA
SET = "geopointset.gpts"

# the number of points of a field of docs/source/tutorials/test.grib
GRIB_POINTS = 104


def _data_file(name):
    return earthkit_test_data_file("geopoints", name)


def _ts(s):
    return np.datetime64(s, "ns")


def _source(name):
    return from_source("file", _data_file(name))


def _bytes(path):
    """The content of the file ``path``, as bytes."""
    with open(path, "rb") as f:
        return f.read()


def _lines(path):
    """The lines of the text file ``path``, without the line endings."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def _write(data, tmp_path, name="out.gpt", **kwargs):
    """Write ``data`` to the file ``name`` of ``tmp_path`` and return the path of the file."""
    path = str(tmp_path / name)
    data.to_target("file", path, **kwargs)
    return path


def _clean(d):
    """A copy of the metadata ``d`` with NaN replaced by a marker, so that dicts compare equal."""
    return {k: ("<nan>" if isinstance(v, float) and v != v else v) for k, v in d.items()}


def _metadata(features):
    """The ``#METADATA`` section of every feature, cleaned with :func:`_clean`."""
    return [_clean(f.metadata()) for f in features]


def _check_points(source, target):
    """Check that the geopoints field ``target`` has the points, the date, the param and the level
    type of ``source``.
    """
    assert target.get("parameter.variable") == source.get("parameter.variable")
    assert target.get("time.valid_datetime") == source.get("time.valid_datetime")
    assert target.get("vertical.level") == source.get("vertical.level")
    assert target.get("vertical.level_type") == source.get("vertical.level_type")
    for name in ["latitude", "longitude"]:
        # the encoder writes the flattened coordinates of the field
        a = np.asarray(getattr(source.geography, f"{name}s")(), dtype="float64").reshape(-1)
        b = np.asarray(getattr(target.geography, f"{name}s")(), dtype="float64").reshape(-1)
        np.testing.assert_array_equal(b, a, err_msg=f"{name}s differ")
    np.testing.assert_array_equal(
        np.asarray(target.values, dtype="float64").reshape(-1),
        np.asarray(source.values, dtype="float64").reshape(-1),
        err_msg="values differ",
    )


# -- the file is copied as it is ----------------------------------------------------------------


@pytest.mark.parametrize("name", GEOPOINTS_FILES)
@pytest.mark.parametrize("target", ["copy.gpt", "copy.txt"])
def test_geopoints_encoder_pass_through_file(name, target, tmp_path):
    """A geopoints file written to a file target is copied byte for byte, without being parsed."""
    source = _data_file(name)
    d = _source(name)
    assert d._reader._parsed is None

    path = _write(d, tmp_path, target)

    assert _bytes(path) == _bytes(source)
    # the copy does not need to know what is in the file
    assert d._reader._parsed is None


@pytest.mark.cache
def test_geopoints_encoder_pass_through_remote(tmp_path):
    """A downloaded geopoints file is also copied as it is."""
    url = earthkit_remote_test_data_file("geopoints", "traditional.gpt")
    d = from_source("url", url)
    assert isinstance(d._reader, GeopointsReader)
    assert d._reader._parsed is None

    path = _write(d, tmp_path, "copy.gpt")

    assert _bytes(path) == _bytes(d.path)
    assert d._reader._parsed is None
    assert_frame_equal(from_source("file", path).to_pandas(), d.to_pandas())


def test_geopoints_encoder_no_pass_through_for_a_subset(tmp_path):
    """A subset of the blocks cannot be copied as it is: the file is parsed and written back."""
    source = _data_file(SET)
    d = _source(SET)
    features = d.to_featurelist("block")
    assert len(features) == 3

    path = _write(features[:2], tmp_path, "subset.gpt")

    assert d._reader._parsed is not None
    assert _bytes(path) != _bytes(source)
    lines = _lines(path)
    # 2 blocks: a geopointset, without the comments of the original file
    assert lines[0] == "#GEOPOINTSET"
    assert lines[1] == "#GEO"
    assert "#METADATA" in lines

    back = from_source("file", path)
    assert back._reader.num_blocks == 2
    assert_frame_equal(back.to_pandas(), features[:2].to_pandas())


def test_geopoints_encoder_no_pass_through_for_all_the_blocks(tmp_path):
    """Even all the blocks of a file go through the encoder, one block at a time."""
    source = _data_file("traditional.gpt")
    d = _source("traditional.gpt")
    rows = len(d.to_pandas())

    path = _write(d.to_featurelist("block"), tmp_path, "all.gpt")
    lines = _lines(path)

    assert _bytes(path) != _bytes(source)
    # exactly one block is written: a geopoints file, not a geopointset, and without the
    # comment lines of the original file
    assert lines[0] == "#GEO"
    assert lines[1] == "#DATA"
    assert len(lines) == 2 + rows
    assert lines[2] == "36.15 -5.35 0 20100810 1200 300.9"
    assert "PARAMETER" not in "\n".join(lines)


# -- featurelists -------------------------------------------------------------------------------


@pytest.mark.parametrize("name", GEOPOINTS_FILES)
def test_geopoints_encoder_block_featurelist_round_trip(name, tmp_path):
    """The blocks of a featurelist are written with their format, columns and metadata."""
    d = _source(name)
    features = d.to_featurelist("block")
    # the last block first, to check that the order of the features is kept
    sel = features[[len(features) - 1, 0]] if len(features) > 1 else features[:1]

    path = _write(sel, tmp_path, "blocks.gpt")
    back = from_source("file", path)

    assert back._reader.num_blocks == len(sel)
    assert back._reader.is_set == (len(sel) != 1)
    assert [f.format for f in back.to_featurelist()] == [f.format for f in sel]
    assert [f.columns for f in back.to_featurelist()] == [f.columns for f in sel]
    assert _metadata(back.to_featurelist()) == _metadata(sel)
    # coordinates, dates, values and missing values
    assert_frame_equal(back.to_pandas(), sel.to_pandas())


@pytest.mark.parametrize("name", GEOPOINTS_FILES)
def test_geopoints_encoder_row_featurelist_round_trip(name, tmp_path):
    """The rows of a row featurelist are merged back into the block they come from."""
    d = _source(name)
    rows = d.to_featurelist("row")
    # two rows of the same block, in the opposite order
    sel = rows[[1, 0]]

    path = _write(sel, tmp_path, "rows.gpt")
    back = from_source("file", path)

    # the rows of one block stay in one block, in the order of the features
    assert back._reader.num_blocks == 1
    assert not back._reader.is_set
    assert back._reader.formats == [rows[0].format]
    assert _metadata(back.to_featurelist()) == [_clean(rows[0].block.metadata)]
    assert_frame_equal(back.to_pandas(), sel.to_pandas())


def test_geopoints_encoder_row_features_of_several_blocks(tmp_path):
    """Rows taken from different blocks are written as one block each."""
    d = _source(SET)
    rows = d.to_featurelist("row")
    assert len(rows) == 8
    # the first row of every block
    sel = rows[[0, 4, 5]]

    path = _write(sel, tmp_path, "jump.gpt")
    lines = _lines(path)
    back = from_source("file", path)

    assert lines[0] == "#GEOPOINTSET"
    assert lines.count("#GEO") == 3
    assert back._reader.num_blocks == 3
    assert _metadata(back.to_featurelist()) == [_clean(f.block.metadata) for f in sel]
    assert_frame_equal(back.to_pandas(), sel.to_pandas())


def test_geopoints_encoder_missing_values(tmp_path):
    """A missing value is written as the missing value of the format, which reads back as NaN."""
    d = _source("missing_latlon.gpt")
    rows = d.to_featurelist("row")
    # the rows with a missing latitude, longitude or both
    sel = rows[[1, 3, 5]]

    path = _write(sel, tmp_path, "missing.gpt")
    lines = _lines(path)

    assert lines[0] == "#GEO"
    assert lines[-3:] == [
        "3e+38 8.8 0.2 20130804 1400 101",
        "47.88 3e+38 0.2 20130804 1200 103",
        "3e+38 3e+38 49 20170814 900 51",
    ]

    df = from_source("file", path).to_pandas()
    assert df["latitude"].isna().tolist() == [True, False, True]
    assert df["longitude"].isna().tolist() == [False, True, True]
    # the time of the block is merged into its date column and written back into both
    assert list(df["date"]) == [_ts("2013-08-04T14:00"), _ts("2013-08-04T12:00"), _ts("2017-08-14T09:00")]
    assert_frame_equal(df, sel.to_pandas())


def test_geopoints_encoder_stnid(tmp_path):
    """A space and a tab of a ``stnid`` are escaped, a backslash cannot be written."""
    good = str(tmp_path / "stnid.gpt")
    with open(good, "w") as f:
        f.write(
            "#GEO\n"
            "#FORMAT NCOLS\n"
            "#COLUMNS\n"
            "stnid latitude longitude date value\n"
            "#DATA\n"
            "heathrow\\32\\airport 1.5 2.5 20130512 3.0\n"
            "oxford\\9\\site 1.5 2.5 20130512 4.0\n"
        )
    d = from_source("file", good)
    assert d.to_pandas()["stnid"].tolist() == ["heathrow airport", "oxford\tsite"]

    path = _write(d.to_featurelist("block"), tmp_path, "stnid_out.gpt")

    assert _lines(path)[-2:] == [
        "heathrow\\32\\airport 1.5 2.5 20130512 3",
        "oxford\\9\\site 1.5 2.5 20130512 4",
    ]
    assert_frame_equal(from_source("file", path).to_pandas(), d.to_pandas())

    # a backslash in a stnid cannot be escaped, so the block cannot be written
    bad = str(tmp_path / "bad_stnid.gpt")
    with open(bad, "w") as f:
        f.write(
            "#GEO\n#FORMAT NCOLS\n#COLUMNS\nstnid latitude longitude date value\n#DATA\nfoo\\bar 1.5 2.5 20130512 3.0\n"
        )
    with pytest.raises(ValueError, match="backslash"):
        from_source("file", bad).to_featurelist("block").to_target("file", str(tmp_path / "bad_out.gpt"))


def test_geopoints_encoder_single_feature(tmp_path):
    """A single block or row feature can be encoded; it is the only way to write one feature."""
    encoder = create_encoder("geopoints")
    d = _source(SET)

    block = encoder.encode(d.to_featurelist("block")[1]).to_bytes()
    assert block == b"#GEO\n#METADATA\nparam=geopotential\n#DATA\n60.82 23.5 0 20130512 600 101045.8\n"

    row = encoder.encode(d.to_featurelist("row")[6]).to_bytes()
    assert row == b"#GEO\n#DATA\n54.33 8.62 0 20130513 0 101027.9101\n"


def test_geopoints_encoder_empty_featurelist(tmp_path):
    """A featurelist without features is an empty geopointset."""
    d = _source(SET)

    path = _write(d.to_featurelist("block")[:0], tmp_path, "empty.gpt")

    assert _bytes(path) == b"#GEOPOINTSET\n"
    back = from_source("file", path)
    assert back._reader.is_set
    assert back._reader.num_blocks == 0
    assert back.to_pandas().empty
    assert len(back.to_featurelist("row")) == 0


def test_geopoints_encoder_metadata(tmp_path):
    """Metadata cannot go into a copy of a file: giving any makes the data be re-encoded."""
    source = _data_file("traditional.gpt")
    d = _source("traditional.gpt")

    path = _write(d, tmp_path, "metadata.gpt", metadata={"author": "me", "param": "t"})
    lines = _lines(path)

    assert d._reader._parsed is not None
    assert _bytes(path) != _bytes(source)
    assert lines[:5] == ["#GEO", "#METADATA", "author=me", "param=t", "#DATA"]

    back = from_source("file", path)
    assert _metadata(back.to_featurelist()) == [{"author": "me", "param": "t"}]
    assert_frame_equal(back.to_pandas(), d.to_pandas())

    # the metadata of the encoder is added to every block, it wins over the one of the block
    encoder = create_encoder("geopoints", metadata={"param": "x", "author": "me"})
    text = encoder.encode(_source(SET)).to_bytes().decode("utf-8")
    assert text.count("param=x") == 3
    assert text.count("author=me") == 3
    assert "geopotential" not in text


# -- multi file readers -------------------------------------------------------------------------


def test_geopoints_encoder_multi_reader(tmp_path):
    """The files of a multi reader are never copied, their blocks are written in order."""
    names = [SET, "xyv.gpt", "ncols_stnid.gpt"]
    paths = [_data_file(n) for n in names]
    d = from_source("file", paths)
    assert d._reader.is_multi
    assert d._reader.num_blocks == 5

    path = _write(d, tmp_path, "multi.gpt")
    lines = _lines(path)
    back = from_source("file", path)

    # the file is a copy of none of the sources
    assert lines[0] == "#GEOPOINTSET"
    assert lines.count("#GEO") == 5
    assert all(_bytes(path) != _bytes(p) for p in paths)

    assert back._reader.num_blocks == d._reader.num_blocks
    assert back._reader.formats == d._reader.formats
    assert_frame_equal(back.to_pandas(), d.to_pandas())
    assert _metadata(back.to_featurelist()) == _metadata(d.to_featurelist())


def test_geopoints_encoder_multi_reader_subset(tmp_path):
    """A subset of the blocks of a multi reader is written like any other featurelist."""
    names = ["traditional.gpt", "xyv.gpt"]
    d = from_source("file", [_data_file(n) for n in names])

    path = _write(d.to_featurelist("block")[:1], tmp_path, "subset.gpt")
    back = from_source("file", path)

    assert not back._reader.is_set
    assert back._reader.num_blocks == 1
    assert back._reader.formats == ["TRADITIONAL"]
    assert_frame_equal(back.to_pandas(), _source("traditional.gpt").to_pandas())


# -- fieldlists and fields ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,num_fields",
    [
        ("traditional.gpt", 1),
        ("missing_latlon.gpt", 1),
        ("ncols.gpt", 4),
        ("polar_vector.gpt", 2),
        (SET, 3),
    ],
)
def test_geopoints_encoder_fieldlist(name, num_fields, tmp_path):
    """A fieldlist is written in the TRADITIONAL format, one block per field."""
    fields = _source(name).to_fieldlist()
    # one field per block and value column
    assert len(fields) == num_fields

    path = _write(fields, tmp_path, "fields.gpt")
    lines = _lines(path)
    back = from_source("file", path)

    assert lines[0] == ("#GEOPOINTSET" if len(fields) != 1 else "#GEO")
    assert lines.count("#GEO") == len(fields)
    assert back._reader.is_set == (len(fields) != 1)
    # a field has no other format than the traditional one
    assert back._reader.formats == ["TRADITIONAL"]
    assert "#FORMAT" not in "\n".join(lines)

    written = back.to_fieldlist()
    assert len(written) == len(fields)
    # the name of the value column of a field becomes the param of its block
    assert [f.get("parameter.variable") for f in written] == [f.get("parameter.variable") for f in fields]
    for source, target in zip(fields, written):
        _check_points(source, target)


def test_geopoints_encoder_single_field(tmp_path):
    """One field is one block, written as a plain geopoints file."""
    d = _source(SET)
    field = d.to_fieldlist()[1]

    path = _write(field, tmp_path, "field.gpt")

    assert _lines(path)[:4] == ["#GEO", "#METADATA", "param=geopotential", "#DATA"]
    written = from_source("file", path).to_fieldlist()
    assert len(written) == 1
    _check_points(field, written[0])


def test_geopoints_encoder_grib_fieldlist(tmp_path):
    """The fields of a GRIB file are written as geopoints blocks."""
    g = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()
    assert len(g) == 2

    path = _write(g, tmp_path, "test.gpt")
    lines = _lines(path)

    # one block per field: the header, the metadata, the #DATA line and the points
    assert len(lines) == 1 + 2 * (5 + GRIB_POINTS)
    assert lines[1:6] == ["#GEO", "#METADATA", "param=2t", "level_type=surface", "#DATA"]

    written = from_source("file", path).to_fieldlist()
    assert len(written) == len(g)
    for source, target in zip(g, written):
        _check_points(source, target)


def test_geopoints_encoder_grib_single_field(tmp_path):
    """A single GRIB field is written as one block, in a plain geopoints file."""
    field = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()[0]

    path = _write(field, tmp_path, "field.gpt")
    lines = _lines(path)

    assert lines[0] == "#GEO"
    assert "#GEOPOINTSET" not in "\n".join(lines)
    assert len(lines) == 5 + GRIB_POINTS
    assert lines[:5] == ["#GEO", "#METADATA", "param=2t", "level_type=surface", "#DATA"]

    written = from_source("file", path).to_fieldlist()
    assert len(written) == 1
    _check_points(field, written[0])


def test_geopoints_encoder_level_type_pressure(tmp_path):
    """A pressure-level fieldlist is written with a level_type and reads back with the same levels."""
    fields = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()
    assert len(fields) == 6

    path = _write(fields, tmp_path, "pl.gpt")
    lines = _lines(path)

    # one level_type entry per block, after the param
    assert lines.count("level_type=pressure") == len(fields)
    assert lines[:6] == ["#GEOPOINTSET", "#GEO", "#METADATA", "param=t", "level_type=pressure", "#DATA"]

    written = from_source("file", path).to_fieldlist()
    assert len(written) == len(fields)
    for source, target in zip(fields, written):
        assert target.get("vertical.level_type") == "pressure"
        assert target.get("vertical.level") == source.get("vertical.level")
        _check_points(source, target)


def test_geopoints_encoder_level_type_pressure_single_field(tmp_path):
    """One pressure-level GRIB field gets a level_type entry in its block."""
    field = from_source("file", earthkit_examples_file("tuv_pl.grib")).to_fieldlist()[0]
    assert field.get("vertical.level_type") == "pressure"

    path = _write(field, tmp_path, "pl_field.gpt")

    assert _lines(path)[:5] == ["#GEO", "#METADATA", "param=t", "level_type=pressure", "#DATA"]
    written = from_source("file", path).to_fieldlist()
    assert len(written) == 1
    _check_points(field, written[0])


@pytest.mark.parametrize(
    "source,level_type",
    [
        (earthkit_examples_file("tuv_pl.grib"), "pressure"),
        (earthkit_test_data_file("t_pl.grib"), "pressure"),
        (earthkit_examples_file("test.grib"), "surface"),
        (earthkit_test_data_file("ml_data.grib"), "hybrid"),
    ],
)
def test_geopoints_encoder_level_type_round_trip(source, level_type, tmp_path):
    """Every known level type is written to #METADATA and restored by to_fieldlist()."""
    fields = from_source("file", source).to_fieldlist()
    assert {f.get("vertical.level_type") for f in fields} == {level_type}

    path = _write(fields, tmp_path, "types.gpt")
    lines = _lines(path)
    assert lines.count(f"level_type={level_type}") == len(fields)

    written = from_source("file", path).to_fieldlist()
    assert len(written) == len(fields)
    for source_field, target in zip(fields, written):
        assert target.get("vertical.level_type") == level_type
        assert target.get("vertical.level") == source_field.get("vertical.level")
        _check_points(source_field, target)


def test_geopoints_encoder_level_type_unknown(tmp_path):
    """A field with the unknown level type gets no level_type entry."""
    field = _source(SET).to_fieldlist()[1]
    assert field.get("vertical.level_type") == "unknown"

    path = _write(field, tmp_path, "unknown.gpt")
    lines = _lines(path)

    assert lines[:4] == ["#GEO", "#METADATA", "param=geopotential", "#DATA"]
    assert "level_type" not in "\n".join(lines)
    written = from_source("file", path).to_fieldlist()
    assert written[0].get("vertical.level_type") == "unknown"
    _check_points(field, written[0])


def test_geopoints_encoder_level_type_missing():
    """A field whose level type is missing (None) gets no level_type entry."""
    from earthkit.data.encoders.geopoints import _field_block

    class _Geography:
        def latitudes(self):
            return np.array([1.0, 2.0])

        def longitudes(self):
            return np.array([10.0, 20.0])

    class _NoMetadataField:
        # a field that has no metadata at all: every key gives the default
        geography = _Geography()

        def to_numpy(self, flatten=True):
            return np.array([3.0, 4.0])

        def get(self, key, default=None):
            return default

    assert _NoMetadataField().get("vertical.level_type", default=None) is None
    block = _field_block(_NoMetadataField(), {})
    assert "level_type" not in block.metadata
    assert not any(line.startswith("level_type") for line in block.header())


def test_geopoints_encoder_level_type_metadata_override(tmp_path):
    """A level_type given as metadata wins over the one of the field."""
    field = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()[0]
    assert field.get("vertical.level_type") == "pressure"

    path = _write(field, tmp_path, "override.gpt", metadata={"level_type": "surface"})
    lines = _lines(path)

    assert lines[:5] == ["#GEO", "#METADATA", "level_type=surface", "param=t", "#DATA"]
    assert "pressure" not in "\n".join(lines)
    written = from_source("file", path).to_fieldlist()
    assert written[0].get("vertical.level_type") == "surface"


# -- choosing the encoder -----------------------------------------------------------------------


def test_geopoints_encoder_gpt_suffix(tmp_path):
    """The ".gpt" suffix of the target selects the encoder, any other name keeps the default one."""
    g = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    geopoints_path = _write(g, tmp_path, "out.gpt")
    assert _lines(geopoints_path)[0] == "#GEOPOINTSET"

    # ".gpts" is not a suffix of the encoder: a fieldlist keeps its own encoder
    other_path = _write(g, tmp_path, "out.gpts")
    assert _bytes(other_path)[:4] == b"GRIB"

    # the encoder can also be given explicitly, whatever the name of the file is
    explicit_path = _write(g, tmp_path, "out.txt", encoder="geopoints")
    assert _bytes(explicit_path) == _bytes(geopoints_path)

    # the same with the top level function
    function_path = str(tmp_path / "function.gpt")
    to_target("file", function_path, data=g)
    assert _bytes(function_path) == _bytes(geopoints_path)


def test_geopoints_encoder_not_implemented():
    """Only data the encoder knows how to write can be encoded."""
    encoder = create_encoder("geopoints")
    d = _source("traditional.gpt")

    with pytest.raises(ValueError, match="No data"):
        encoder.encode()

    with pytest.raises(NotImplementedError, match="template"):
        encoder.encode(d, template=d)

    with pytest.raises(NotImplementedError, match="foo"):
        encoder.encode(d, foo=1)

    with pytest.raises(NotImplementedError, match="DataFrame"):
        encoder.encode(d.to_pandas())

    with pytest.raises(NotImplementedError, match="Dataset"):
        encoder.encode(d.to_xarray())


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
