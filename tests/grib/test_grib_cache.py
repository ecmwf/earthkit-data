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
from earthkit.data.utils.diag import field_cache_diag
from earthkit.data.utils.diag import metadata_cache_diag
from earthkit.data.utils.testing import earthkit_examples_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402

FIELD_NUM = 18
MD_ITEM_NUM = 7

# NOTE: the grib_cache has been refactored for version 1.0.0. These test have not been fully
# adjusted so far. With the new implementation thr grib handle management can only be monitored when the
# grib-handle-policy is set to "cache". So the tests are currently fully testing the metadata cache and
# only not partly the grib handle management.


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
    from earthkit.data.field.grib.metadata import MetadataCacheHandler

    def patched_make_metadata_cache():
        return TestMetadataCache()

    monkeypatch.setattr(MetadataCacheHandler, "make_default_cache", patched_make_metadata_cache)


def _check_diag(diag, ref):
    for k, v in ref.items():
        assert diag[k] == v, f"{k}={diag[k]} != {v}"


@pytest.mark.parametrize("handle_cache_size", [1, 5])
@pytest.mark.parametrize("serialise", [True, False])
def test_grib_cache_basic_file_patched(handle_cache_size, serialise, patch_metadata_cache):

    with config.temporary(
        {
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": handle_cache_size,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))

        if serialise:
            pickled_f = pickle.dumps(ds)
            ds = pickle.loads(pickled_f)

        assert len(ds) == FIELD_NUM

        # unique values
        ref_vals = ds.unique(
            "metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime"
        )

        ref = {
            "handle_cache_size": handle_cache_size,
            "handle_create_count": FIELD_NUM,
            # "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }
        _check_diag(ds._diag(), ref)

        for _ in ds:
            pass

        _check_diag(ds._diag(), ref)

        # unique values repeated
        vals = ds.unique(
            "metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime"
        )

        assert vals == ref_vals

        ref = {
            "handle_cache_size": handle_cache_size,
            "handle_create_count": FIELD_NUM,
            # "current_handle_count": 0,
            "metadata_cache_hits": FIELD_NUM * 4,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }
        _check_diag(ds._diag(), ref)

        # order by
        ds.order_by(["metadata.levelist", "metadata.valid_datetime", "metadata.paramId", "metadata.levtype"])
        ref = {
            "handle_cache_size": handle_cache_size,
            "handle_create_count": FIELD_NUM,
            # "current_handle_count": 0,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }
        diag = ds._diag()
        _check_diag(diag, ref)

        assert diag["metadata_cache_hits"] >= FIELD_NUM * 4


def test_grib_cache_basic_file_non_patched():
    """This test is the same as test_grib_cache_basic but without the patch_metadata_cache fixture.
    So metadata cache hits and misses are not counted."""

    with config.temporary(
        {
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == FIELD_NUM

        # unique values
        ref_vals = ds.unique(
            "metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime"
        )

        ref = {
            "handle_cache_size": 1,
            "handle_create_count": FIELD_NUM,
            # "current_handle_count": 0,
            # "metadata_cache_hits": 0,
            # "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }
        _check_diag(ds._diag(), ref)

        # unique values repeated
        vals = ds.unique(
            "metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime"
        )

        assert vals == ref_vals

        ref = {
            "handle_cache_size": 1,
            "handle_create_count": FIELD_NUM,
            # "current_handle_count": 0,
            # "metadata_cache_hits": FIELD_NUM * 4,
            # "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }
        _check_diag(ds._diag(), ref)

        # order by
        ds.order_by(["metadata.levelist", "metadata.valid_datetime", "metadata.paramId", "metadata.levtype"])
        ref = {
            "handle_cache_size": 1,
            "handle_create_count": FIELD_NUM,
            # "current_handle_count": 0,
            # "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }
        _check_diag(ds._diag(), ref)


# TODO: decide if it should be working for fl_type="array" and "memory"
@pytest.mark.parametrize("serialise", [True, False])
@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_cache_basic_metadata_patched(serialise, fl_type, patch_metadata_cache):

    with config.temporary(
        {
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds, _ = load_grib_data("tuv_pl.grib", fl_type)

        if serialise:
            pickled_f = pickle.dumps(ds)
            ds = pickle.loads(pickled_f)

        assert len(ds) == FIELD_NUM

        # unique values
        ref_vals = ds.unique(
            "metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime"
        )

        ref = {
            "metadata_cache_hits": 0,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }

        diag = metadata_cache_diag(ds)
        _check_diag(diag, ref)

        # unique values repeated
        vals = ds.unique(
            "metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime"
        )

        assert vals == ref_vals

        ref = {
            "metadata_cache_hits": FIELD_NUM * 4,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }
        diag = metadata_cache_diag(ds)
        _check_diag(diag, ref)

        # order by
        ds.order_by(["metadata.levelist", "metadata.valid_datetime", "metadata.paramId", "metadata.levtype"])
        ref = {
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }
        diag = metadata_cache_diag(ds)
        _check_diag(diag, ref)

        assert diag["metadata_cache_hits"] >= FIELD_NUM * 4


def test_grib_cache_options_1(patch_metadata_cache):
    with config.temporary(
        {
            "grib-handle-policy": "temporary",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == FIELD_NUM

        # unique values
        ds.unique("metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime")

        # assert ds._field_manager.cache is not None
        # assert ds._handle_manager.cache is None

        ref = {
            # "handle_create_count": FIELD_NUM * 6,
            # "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }

        _check_diag(ds._diag(), ref)

        # keep a reference to the field
        first = ds[0]

        _check_diag(
            field_cache_diag(first),
            {
                "metadata_cache_hits": 0,
                "metadata_cache_misses": MD_ITEM_NUM,
                "metadata_cache_size": MD_ITEM_NUM,
            },
        )

        # key already cached
        first.get("metadata.levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {
                "metadata_cache_hits": 1,
                "metadata_cache_misses": MD_ITEM_NUM,
                "metadata_cache_size": MD_ITEM_NUM,
            },
        )

        ref["metadata_cache_hits"] += 1
        _check_diag(ds._diag(), ref)

        # uncached key
        first.get("metadata.level", default=None)
        _check_diag(
            field_cache_diag(first),
            {
                "metadata_cache_hits": 1,
                "metadata_cache_misses": MD_ITEM_NUM + 1,
                "metadata_cache_size": MD_ITEM_NUM + 1,
            },
        )

        # ref["handle_create_count"] += 1
        ref["metadata_cache_misses"] += 1
        ref["metadata_cache_size"] += 1
        _check_diag(ds._diag(), ref)


def test_grib_cache_options_2(patch_metadata_cache):
    with config.temporary(
        {
            "grib-handle-policy": "persistent",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == FIELD_NUM

        # unique values
        ds.unique("metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime")

        # assert ds._field_manager.cache is not None
        # assert ds._handle_manager.cache is None

        ref = {
            # "handle_create_count": FIELD_NUM,
            # "current_handle_count": FIELD_NUM,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }

        _check_diag(ds._diag(), ref)

        # keep a reference to the field
        first = ds[0]

        _check_diag(ds._diag(), ref)

        _check_diag(
            field_cache_diag(first),
            {
                "metadata_cache_hits": 0,
                "metadata_cache_misses": MD_ITEM_NUM,
                "metadata_cache_size": MD_ITEM_NUM,
            },
        )

        # key already cached
        first.get("metadata.levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {
                "metadata_cache_hits": 1,
                "metadata_cache_misses": MD_ITEM_NUM,
                "metadata_cache_size": MD_ITEM_NUM,
            },
        )

        ref["metadata_cache_hits"] += 1
        _check_diag(ds._diag(), ref)

        # uncached key
        first.get("metadata.level", default=None)
        _check_diag(
            field_cache_diag(first),
            {
                "metadata_cache_hits": 1,
                "metadata_cache_misses": MD_ITEM_NUM + 1,
                "metadata_cache_size": MD_ITEM_NUM + 1,
            },
        )

        ref["metadata_cache_misses"] += 1
        ref["metadata_cache_size"] += 1
        _check_diag(ds._diag(), ref)


def test_grib_cache_options_3(patch_metadata_cache):
    with config.temporary(
        {
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == FIELD_NUM

        # unique values
        ds.unique("metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime")

        # assert ds._field_manager.cache is not None
        # assert ds._handle_manager.cache is not None

        ref = {
            "handle_cache_size": 1,
            "handle_create_count": FIELD_NUM,
            # "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }

        _check_diag(ds._diag(), ref)

        # keep a reference to the field
        first = ds[0]

        _check_diag(
            field_cache_diag(first),
            {
                "metadata_cache_hits": 0,
                "metadata_cache_misses": MD_ITEM_NUM,
                "metadata_cache_size": MD_ITEM_NUM,
            },
        )

        # key already cached
        first.get("metadata.levelist", default=None)
        _check_diag(
            field_cache_diag(first),
            {
                "metadata_cache_hits": 1,
                "metadata_cache_misses": MD_ITEM_NUM,
                "metadata_cache_size": MD_ITEM_NUM,
            },
        )

        ref["metadata_cache_hits"] += 1
        _check_diag(ds._diag(), ref)

        # uncached key
        first.get("metadata.level", default=None)
        _check_diag(
            field_cache_diag(first),
            {
                "metadata_cache_hits": 1,
                "metadata_cache_misses": MD_ITEM_NUM + 1,
                "metadata_cache_size": MD_ITEM_NUM + 1,
            },
        )

        ref["handle_create_count"] += 1
        ref["metadata_cache_misses"] += 1
        ref["metadata_cache_size"] += 1
        _check_diag(ds._diag(), ref)


# TODO: decide if it should be working for fl_type="array"
@pytest.mark.parametrize("fl_type", ["file", "memory"])
def test_grib_cache_metadata_use_kwargs_1(fl_type, patch_metadata_cache):
    with config.temporary(
        {
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": False,
        }
    ):

        _kwargs = {
            "use_grib_metadata_cache": True,
        }

        ds, _ = load_grib_data("tuv_pl.grib", fl_type, **_kwargs)

        assert len(ds) == FIELD_NUM

        # unique values
        ds.unique("metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime")

        ref = {
            "metadata_cache_hits": 0,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }

        diag = metadata_cache_diag(ds)
        _check_diag(diag, ref)

        # unique values
        ds.unique("metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime")

        ref = {
            "metadata_cache_hits": FIELD_NUM * 4,
            "metadata_cache_misses": FIELD_NUM * MD_ITEM_NUM,
            "metadata_cache_size": FIELD_NUM * MD_ITEM_NUM,
        }

        diag = metadata_cache_diag(ds)
        _check_diag(diag, ref)


# TODO: decide if it should be working for fl_type="array"
@pytest.mark.parametrize("fl_type", ["file", "memory"])
def test_grib_cache_metadata_use_kwargs_2(fl_type, patch_metadata_cache):
    with config.temporary(
        {
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):

        _kwargs = {
            "use_grib_metadata_cache": False,
        }

        ds, _ = load_grib_data("tuv_pl.grib", fl_type, **_kwargs)

        assert len(ds) == FIELD_NUM

        # unique values
        ds.unique("metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime")

        ref = {
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 0,
            "metadata_cache_size": 0,
        }

        diag = metadata_cache_diag(ds)
        _check_diag(diag, ref)

        # unique values
        ds.unique("metadata.paramId", "metadata.levelist", "metadata.levtype", "metadata.valid_datetime")

        ref = {
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 0,
            "metadata_cache_size": 0,
        }

        diag = metadata_cache_diag(ds)
        _check_diag(diag, ref)
