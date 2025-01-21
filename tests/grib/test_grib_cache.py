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
import sys

import pytest

from earthkit.data import config
from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.utils.diag import field_cache_diag

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


class TestMetadataCache:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.data = {}

    def __contains__(self, key):
        return key in self.data

    def __getitem__(self, key):
        self.hits += 1
        return self.data[key]

    def __setitem__(self, key, value):
        self.misses += 1
        self.data[key] = value

    def __len__(self):
        return len(self.data)


@pytest.fixture
def patch_metadata_cache(monkeypatch):
    from earthkit.data.readers.grib.codes import GribField

    def patched_make_metadata_cache(self):
        return TestMetadataCache()

    monkeypatch.setattr(GribField, "_make_metadata_cache", patched_make_metadata_cache)


def _check_diag(diag, ref):
    for k, v in ref.items():
        assert diag[k] == v, f"{k}={diag[k]} != {v}"


@pytest.mark.parametrize("handle_cache_size", [1, 5])
@pytest.mark.parametrize("serialise", [True, False])
def test_grib_cache_basic_file_patched(handle_cache_size, serialise, patch_metadata_cache):

    with config.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": handle_cache_size,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))

        if serialise:
            pickled_f = pickle.dumps(ds)
            ds = pickle.loads(pickled_f)

        assert len(ds) == 18

        # unique values
        ref_vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        # for f in ds:
        #     print(f.metadata()._cache.data)

        diag = ds._cache_diag()
        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_cache_size": handle_cache_size,
            "handle_create_count": 18,
            "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._cache_diag(), ref)

        for i, f in enumerate(ds):
            assert i in ds._field_manager.cache, f"{i} not in cache"
            assert id(f) == id(ds._field_manager.cache[i]), f"{i} not the same object"

        _check_diag(ds._cache_diag(), ref)

        # unique values repeated
        vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert vals == ref_vals

        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_cache_size": handle_cache_size,
            "handle_create_count": 18,
            "current_handle_count": 0,
            "metadata_cache_hits": 18 * 4,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._cache_diag(), ref)

        # order by
        ds.order_by(["levelist", "valid_datetime", "paramId", "levtype"])
        diag = ds._cache_diag()
        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_cache_size": handle_cache_size,
            "handle_create_count": 18,
            "current_handle_count": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._cache_diag(), ref)

        assert diag["metadata_cache_hits"] >= 18 * 4

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0].handle == md._handle


def test_grib_cache_basic_file_non_patched():
    """This test is the same as test_grib_cache_basic but without the patch_metadata_cache fixture.
    So metadata cache hits and misses are not counted."""

    with config.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        # unique values
        ref_vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_cache_size": 1,
            "handle_create_count": 18,
            "current_handle_count": 0,
            # "metadata_cache_hits": 0,
            # "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._cache_diag(), ref)

        for i, f in enumerate(ds):
            assert i in ds._field_manager.cache, f"{i} not in cache"
            assert id(f) == id(ds._field_manager.cache[i]), f"{i} not the same object"

        _check_diag(ds._cache_diag(), ref)

        # unique values repeated
        vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert vals == ref_vals

        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_cache_size": 1,
            "handle_create_count": 18,
            "current_handle_count": 0,
            # "metadata_cache_hits": 18 * 4,
            # "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._cache_diag(), ref)

        # order by
        ds.order_by(["levelist", "valid_datetime", "paramId", "levtype"])
        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_cache_size": 1,
            "handle_create_count": 18,
            "current_handle_count": 0,
            # "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._cache_diag(), ref)

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0].handle == md._handle


@pytest.mark.parametrize("serialise", [True, False])
@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
def test_grib_cache_basic_metadata_patched(serialise, fl_type, patch_metadata_cache):

    with config.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds, _ = load_grib_data("tuv_pl.grib", fl_type)

        if serialise:
            pickled_f = pickle.dumps(ds)
            ds = pickle.loads(pickled_f)

        assert len(ds) == 18

        # unique values
        ref_vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        # for f in ds:
        #     print(f.metadata()._cache.data)

        diag = ds._cache_diag()
        ref = {
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._cache_diag(), ref)

        # unique values repeated
        vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert vals == ref_vals

        ref = {
            "metadata_cache_hits": 18 * 4,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._cache_diag(), ref)

        # order by
        ds.order_by(["levelist", "valid_datetime", "paramId", "levtype"])
        diag = ds._cache_diag()
        ref = {
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._cache_diag(), ref)

        assert diag["metadata_cache_hits"] >= 18 * 4

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        if fl_type != "array":
            # handle is taken from the field
            assert hasattr(md, "_field")
            assert ds[0].handle == md._handle
        else:
            # handle is not taken from the metadata
            assert not hasattr(md, "_field")
            assert ds[0].handle == md._handle


def test_grib_cache_options_1(patch_metadata_cache):
    with config.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "temporary",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert ds._field_manager.cache is not None
        assert ds._handle_manager.cache is None

        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_create_count": 18 * 5,
            "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }

        _check_diag(ds._cache_diag(), ref)

        for i, f in enumerate(ds):
            assert i in ds._field_manager.cache, f"{i} not in cache"
            assert id(f) == id(ds._field_manager.cache[i]), f"{i} not the same object"

        _check_diag(ds._cache_diag(), ref)

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle is None

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is None

        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 6, "metadata_cache_size": 6},
        )

        # key already cached
        first.metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 1, "metadata_cache_misses": 6, "metadata_cache_size": 6},
        )

        ref["metadata_cache_hits"] += 1
        _check_diag(ds._cache_diag(), ref)

        # uncached key
        first.metadata("level")
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 1, "metadata_cache_misses": 7, "metadata_cache_size": 7},
        )

        ref["handle_create_count"] += 1
        ref["metadata_cache_misses"] += 1
        ref["metadata_cache_size"] += 1
        _check_diag(ds._cache_diag(), ref)

        assert first.handle != md._handle

        ref["handle_create_count"] += 2
        _check_diag(ds._cache_diag(), ref)


def test_grib_cache_options_2(patch_metadata_cache):
    with config.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "persistent",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert ds._field_manager.cache is not None
        assert ds._handle_manager.cache is None

        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_create_count": 18,
            "current_handle_count": 18,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }

        _check_diag(ds._cache_diag(), ref)

        for i, f in enumerate(ds):
            assert i in ds._field_manager.cache, f"{i} not in cache"
            assert id(f) == id(ds._field_manager.cache[i]), f"{i} not the same object"

        _check_diag(ds._cache_diag(), ref)

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle is not None

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is not None
        assert first._handle == md._handle
        assert first.handle == first._handle

        _check_diag(ds._cache_diag(), ref)

        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 6, "metadata_cache_size": 6},
        )

        # key already cached
        first.metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 1, "metadata_cache_misses": 6, "metadata_cache_size": 6},
        )

        ref["metadata_cache_hits"] += 1
        _check_diag(ds._cache_diag(), ref)

        # uncached key
        first.metadata("level")
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 1, "metadata_cache_misses": 7, "metadata_cache_size": 7},
        )

        ref["metadata_cache_misses"] += 1
        ref["metadata_cache_size"] += 1
        _check_diag(ds._cache_diag(), ref)

        assert first.handle == md._handle

        _check_diag(ds._cache_diag(), ref)


def test_grib_cache_options_3(patch_metadata_cache):
    with config.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert ds._field_manager.cache is not None
        assert ds._handle_manager.cache is not None

        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_cache_size": 1,
            "handle_create_count": 18,
            "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }

        _check_diag(ds._cache_diag(), ref)

        for i, f in enumerate(ds):
            assert i in ds._field_manager.cache, f"{i} not in cache"
            assert id(f) == id(ds._field_manager.cache[i]), f"{i} not the same object"

        _check_diag(ds._cache_diag(), ref)

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle is None

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is None

        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 6, "metadata_cache_size": 6},
        )

        # key already cached
        first.metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 1, "metadata_cache_misses": 6, "metadata_cache_size": 6},
        )

        ref["metadata_cache_hits"] += 1
        _check_diag(ds._cache_diag(), ref)

        # uncached key
        first.metadata("level")
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 1, "metadata_cache_misses": 7, "metadata_cache_size": 7},
        )

        ref["handle_create_count"] += 1
        ref["metadata_cache_misses"] += 1
        ref["metadata_cache_size"] += 1
        _check_diag(ds._cache_diag(), ref)

        assert first.handle == md._handle

        _check_diag(ds._cache_diag(), ref)


def test_grib_cache_options_4(patch_metadata_cache):
    with config.temporary(
        {
            "grib-field-policy": "temporary",
            "grib-handle-policy": "temporary",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        ref = {
            "field_cache_size": 0,
            "field_create_count": 18,
            "handle_cache_size": 0,
            "handle_create_count": 18 * 5,
            "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 0,
            "metadata_cache_size": 0,
        }

        _check_diag(ds._cache_diag(), ref)

        assert ds._field_manager.cache is None
        assert ds._handle_manager.cache is None

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle != md._handle
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is None
        ref["field_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )

        first.metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 1, "metadata_cache_size": 1},
        )

        first.metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 1, "metadata_cache_misses": 1, "metadata_cache_size": 1},
        )

        ref["handle_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        # repeat with indexed field
        _check_diag(
            field_cache_diag(ds[0]),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )

        ref["field_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(ds[0]),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )

        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(ds[0]),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )

        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)


def test_grib_cache_options_5(patch_metadata_cache):
    with config.temporary(
        {
            "grib-field-policy": "temporary",
            "grib-handle-policy": "persistent",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        ref = {
            "field_cache_size": 0,
            "field_create_count": 18,
            "handle_cache_size": 0,
            "handle_create_count": 18,
            "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 0,
            "metadata_cache_size": 0,
        }

        _check_diag(ds._cache_diag(), ref)

        assert ds._field_manager.cache is None
        assert ds._handle_manager.cache is None

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle != md._handle
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is None
        ref["field_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )

        first.metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 1, "metadata_cache_size": 1},
        )

        assert first._handle is not None

        first.metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 1, "metadata_cache_misses": 1, "metadata_cache_size": 1},
        )

        assert first._handle is not None

        ref["handle_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        # repeat with indexed field
        _check_diag(
            field_cache_diag(ds[0]),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )

        ref["field_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(ds[0]),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(ds[0]),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)


def test_grib_cache_options_6(patch_metadata_cache):
    with config.temporary(
        {
            "grib-field-policy": "temporary",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        ref = {
            "field_cache_size": 0,
            "field_create_count": 18,
            "handle_cache_size": 1,
            "handle_create_count": 18,
            "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 0,
            "metadata_cache_size": 0,
        }

        _check_diag(ds._cache_diag(), ref)

        assert ds._field_manager.cache is None
        assert ds._handle_manager.cache is not None

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle != md._handle
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is None
        ref["field_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )

        first.metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 1, "metadata_cache_size": 1},
        )

        first.metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {"metadata_cache_hits": 1, "metadata_cache_misses": 1, "metadata_cache_size": 1},
        )

        _check_diag(ds._cache_diag(), ref)

        # repeat with indexed field
        _check_diag(
            field_cache_diag(ds[0]),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )

        ref["field_create_count"] += 1
        _check_diag(ds._cache_diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(ds[0]),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )
        ref["field_create_count"] += 2
        _check_diag(ds._cache_diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            field_cache_diag(ds[0]),
            {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0},
        )
        ref["field_create_count"] += 2
        _check_diag(ds._cache_diag(), ref)


def test_grib_cache_file_use_kwargs_1():
    _kwargs = {
        "grib_field_policy": "temporary",
        "grib_handle_policy": "persistent",
        "grib_handle_cache_size": 1,
        "use_grib_metadata_cache": True,
    }

    ds = from_source("file", earthkit_examples_file("tuv_pl.grib"), **_kwargs)
    assert len(ds) == 18

    # unique values
    ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

    ref = {
        "field_cache_size": 0,
        "field_create_count": 18,
        "handle_cache_size": 0,
        "handle_create_count": 18,
        "current_handle_count": 0,
        "metadata_cache_hits": 0,
        "metadata_cache_misses": 0,
        "metadata_cache_size": 0,
    }

    _check_diag(ds._cache_diag(), ref)


def test_grib_cache_file_use_kwargs_2():
    _kwargs = {
        "grib-field-policy": "temporary",
        "grib_handle_policy": "persistent",
        "grib_handle_cache_size": 1,
        "use_grib_metadata_cache": True,
    }

    with pytest.raises(KeyError):
        from_source("file", earthkit_examples_file("tuv_pl.grib"), **_kwargs)


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
def test_grib_cache_metadata_use_kwargs_1(fl_type, patch_metadata_cache):
    with config.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": False,
        }
    ):

        _kwargs = {
            "use_grib_metadata_cache": True,
        }

        ds, _ = load_grib_data("tuv_pl.grib", fl_type, **_kwargs)

        assert len(ds) == 18

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        ref = {
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 108,
            "metadata_cache_size": 108,
        }

        _check_diag(ds._cache_diag(), ref)

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        ref = {
            "metadata_cache_hits": 72,
            "metadata_cache_misses": 108,
            "metadata_cache_size": 108,
        }

        _check_diag(ds._cache_diag(), ref)


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
def test_grib_cache_metadata_use_kwargs_2(fl_type, patch_metadata_cache):
    with config.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):

        _kwargs = {
            "use_grib_metadata_cache": False,
        }

        ds, _ = load_grib_data("tuv_pl.grib", fl_type, **_kwargs)

        assert len(ds) == 18

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        ref = {
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 0,
            "metadata_cache_size": 0,
        }

        _check_diag(ds._cache_diag(), ref)

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        ref = {
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 0,
            "metadata_cache_size": 0,
        }

        _check_diag(ds._cache_diag(), ref)
