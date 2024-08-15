#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data import from_source
from earthkit.data import settings
from earthkit.data.testing import earthkit_examples_file


def _check_diag(diag, ref):
    for k, v in ref.items():
        assert diag[k] == v, f"{k}={diag[k]} != {v}"


@pytest.mark.parametrize("handle_cache_size", [1, 5])
def test_grib_cache_basic(handle_cache_size):

    with settings.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": handle_cache_size,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._manager
        assert cache

        # unique values
        ref_vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        diag = ds._diag()
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
        _check_diag(ds._diag(), ref)

        for i, f in enumerate(ds):
            assert i in cache.field_cache, f"{i} not in cache"
            assert id(f) == id(cache.field_cache[i]), f"{i} not the same object"

        _check_diag(ds._diag(), ref)

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
        _check_diag(ds._diag(), ref)

        # order by
        ds.order_by(["levelist", "valid_datetime", "paramId", "levtype"])
        diag = ds._diag()
        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_cache_size": handle_cache_size,
            "handle_create_count": 18,
            "current_handle_count": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        _check_diag(ds._diag(), ref)

        assert diag["metadata_cache_hits"] >= 18 * 4

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0].handle == md._handle


def test_grib_cache_options_1():
    with settings.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "temporary",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._manager
        assert cache

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert cache.field_cache is not None
        assert cache.handle_cache is None

        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_create_count": 18 * 5,
            "current_handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }

        _check_diag(ds._diag(), ref)

        for i, f in enumerate(ds):
            assert i in cache.field_cache, f"{i} not in cache"
            assert id(f) == id(cache.field_cache[i]), f"{i} not the same object"

        _check_diag(ds._diag(), ref)

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
            first._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 6, "metadata_cache_size": 6}
        )

        # key already cached
        first.metadata("levelist", default=None)
        _check_diag(
            first._diag(), {"metadata_cache_hits": 1, "metadata_cache_misses": 6, "metadata_cache_size": 6}
        )

        ref["metadata_cache_hits"] += 1
        _check_diag(ds._diag(), ref)

        # uncached key
        first.metadata("level")
        _check_diag(
            first._diag(), {"metadata_cache_hits": 1, "metadata_cache_misses": 7, "metadata_cache_size": 7}
        )

        ref["handle_create_count"] += 1
        ref["metadata_cache_misses"] += 1
        ref["metadata_cache_size"] += 1
        _check_diag(ds._diag(), ref)

        assert first.handle != md._handle

        ref["handle_create_count"] += 2
        _check_diag(ds._diag(), ref)


def test_grib_cache_options_2():
    with settings.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "persistent",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._manager
        assert cache

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert cache.field_cache is not None
        assert cache.handle_cache is None

        ref = {
            "field_cache_size": 18,
            "field_create_count": 18,
            "handle_create_count": 18,
            "current_handle_count": 18,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }

        _check_diag(ds._diag(), ref)

        for i, f in enumerate(ds):
            assert i in cache.field_cache, f"{i} not in cache"
            assert id(f) == id(cache.field_cache[i]), f"{i} not the same object"

        _check_diag(ds._diag(), ref)

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

        _check_diag(ds._diag(), ref)

        _check_diag(
            first._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 6, "metadata_cache_size": 6}
        )

        # key already cached
        first.metadata("levelist", default=None)
        _check_diag(
            first._diag(), {"metadata_cache_hits": 1, "metadata_cache_misses": 6, "metadata_cache_size": 6}
        )

        ref["metadata_cache_hits"] += 1
        _check_diag(ds._diag(), ref)

        # uncached key
        first.metadata("level")
        _check_diag(
            first._diag(), {"metadata_cache_hits": 1, "metadata_cache_misses": 7, "metadata_cache_size": 7}
        )

        ref["metadata_cache_misses"] += 1
        ref["metadata_cache_size"] += 1
        _check_diag(ds._diag(), ref)

        assert first.handle == md._handle

        _check_diag(ds._diag(), ref)


def test_grib_cache_options_3():
    with settings.temporary(
        {
            "grib-field-policy": "persistent",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._manager
        assert cache

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert cache.field_cache is not None
        assert cache.handle_cache is not None

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

        _check_diag(ds._diag(), ref)

        for i, f in enumerate(ds):
            assert i in cache.field_cache, f"{i} not in cache"
            assert id(f) == id(cache.field_cache[i]), f"{i} not the same object"

        _check_diag(ds._diag(), ref)

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
            first._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 6, "metadata_cache_size": 6}
        )

        # key already cached
        first.metadata("levelist", default=None)
        _check_diag(
            first._diag(), {"metadata_cache_hits": 1, "metadata_cache_misses": 6, "metadata_cache_size": 6}
        )

        ref["metadata_cache_hits"] += 1
        _check_diag(ds._diag(), ref)

        # uncached key
        first.metadata("level")
        _check_diag(
            first._diag(), {"metadata_cache_hits": 1, "metadata_cache_misses": 7, "metadata_cache_size": 7}
        )

        ref["handle_create_count"] += 1
        ref["metadata_cache_misses"] += 1
        ref["metadata_cache_size"] += 1
        _check_diag(ds._diag(), ref)

        assert first.handle == md._handle

        _check_diag(ds._diag(), ref)


def test_grib_cache_options_4():
    with settings.temporary(
        {
            "grib-field-policy": "temporary",
            "grib-handle-policy": "temporary",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._manager
        assert cache

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

        _check_diag(ds._diag(), ref)

        assert cache.field_cache is None
        assert cache.handle_cache is None

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle != md._handle
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._diag(), ref)

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is None
        ref["field_create_count"] += 1
        _check_diag(ds._diag(), ref)

        _check_diag(
            first._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )

        first.metadata("levelist", default=None)
        _check_diag(
            first._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 1, "metadata_cache_size": 1}
        )

        first.metadata("levelist", default=None)
        _check_diag(
            first._diag(), {"metadata_cache_hits": 1, "metadata_cache_misses": 1, "metadata_cache_size": 1}
        )

        ref["handle_create_count"] += 1
        _check_diag(ds._diag(), ref)

        # repeat with indexed field
        _check_diag(
            ds[0]._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )

        ref["field_create_count"] += 1
        _check_diag(ds._diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            ds[0]._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            ds[0]._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._diag(), ref)


def test_grib_cache_options_5():
    with settings.temporary(
        {
            "grib-field-policy": "temporary",
            "grib-handle-policy": "persistent",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._manager
        assert cache

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

        _check_diag(ds._diag(), ref)

        assert cache.field_cache is None
        assert cache.handle_cache is None

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle != md._handle
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._diag(), ref)

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is None
        ref["field_create_count"] += 1
        _check_diag(ds._diag(), ref)

        _check_diag(
            first._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )

        first.metadata("levelist", default=None)
        _check_diag(
            first._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 1, "metadata_cache_size": 1}
        )

        assert first._handle is not None

        first.metadata("levelist", default=None)
        _check_diag(
            first._diag(), {"metadata_cache_hits": 1, "metadata_cache_misses": 1, "metadata_cache_size": 1}
        )

        assert first._handle is not None

        ref["handle_create_count"] += 1
        _check_diag(ds._diag(), ref)

        # repeat with indexed field
        _check_diag(
            ds[0]._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )

        ref["field_create_count"] += 1
        _check_diag(ds._diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            ds[0]._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            ds[0]._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._diag(), ref)


def test_grib_cache_options_6():
    with settings.temporary(
        {
            "grib-field-policy": "temporary",
            "grib-handle-policy": "cache",
            "grib-handle-cache-size": 1,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._manager
        assert cache

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

        _check_diag(ds._diag(), ref)

        assert cache.field_cache is None
        assert cache.handle_cache is not None

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle != md._handle
        ref["field_create_count"] += 2
        ref["handle_create_count"] += 1
        _check_diag(ds._diag(), ref)

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is None
        ref["field_create_count"] += 1
        _check_diag(ds._diag(), ref)

        _check_diag(
            first._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )

        first.metadata("levelist", default=None)
        _check_diag(
            first._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 1, "metadata_cache_size": 1}
        )

        first.metadata("levelist", default=None)
        _check_diag(
            first._diag(), {"metadata_cache_hits": 1, "metadata_cache_misses": 1, "metadata_cache_size": 1}
        )

        _check_diag(ds._diag(), ref)

        # repeat with indexed field
        _check_diag(
            ds[0]._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )

        ref["field_create_count"] += 1
        _check_diag(ds._diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            ds[0]._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )
        ref["field_create_count"] += 2
        _check_diag(ds._diag(), ref)

        ds[0].metadata("levelist", default=None)
        _check_diag(
            ds[0]._diag(), {"metadata_cache_hits": 0, "metadata_cache_misses": 0, "metadata_cache_size": 0}
        )
        ref["field_create_count"] += 2
        _check_diag(ds._diag(), ref)


def test_grib_cache_use_kwargs_1():
    _kwargs = {
        "grib_field_policy": "temporary",
        "grib_handle_policy": "persistent",
        "grib_handle_cache_size": 1,
        "use_grib_metadata_cache": True,
    }

    ds = from_source("file", earthkit_examples_file("tuv_pl.grib"), **_kwargs)
    assert len(ds) == 18

    cache = ds._manager
    assert cache

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

    _check_diag(ds._diag(), ref)


def test_grib_cache_use_kwargs_2():
    _kwargs = {
        "grib-field-policy": "temporary",
        "grib_handle_policy": "persistent",
        "grib_handle_cache_size": 1,
        "use_grib_metadata_cache": True,
    }

    with pytest.raises(KeyError):
        from_source("file", earthkit_examples_file("tuv_pl.grib"), **_kwargs)
