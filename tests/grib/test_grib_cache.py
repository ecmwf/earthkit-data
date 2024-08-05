#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data import from_source
from earthkit.data import settings
from earthkit.data.testing import earthkit_examples_file


def test_grib_cache_1():

    with settings.temporary(
        {"grib-field-cache": True, "grib-handle-cache-size": 10, "grib-metadata-cache": True}
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        # unique values
        ref_vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert len(ds._field_cache) == 18
        assert len(ds._handle_cache) == 10

        diag = ds._diag()
        ref = {
            "handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        for i, f in enumerate(ds):
            assert i in ds._field_cache, f"{i} not in cache"
            assert id(f) == id(ds._field_cache[i]), f"{i} not the same object"

        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        # unique values repeated
        vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert len(ds._field_cache) == 18
        assert len(ds._handle_cache) == 10

        assert vals == ref_vals
        diag = ds._diag()
        ref = {
            "handle_count": 0,
            "metadata_cache_hits": 18 * 4,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        # order by
        ds.order_by(["levelist", "valid_datetime", "paramId", "levtype"])
        assert len(ds._field_cache) == 18
        assert len(ds._handle_cache) == 10
        diag = ds._diag()
        assert diag["handle_count"] == 0
        assert diag["metadata_cache_hits"] >= 18 * 4
        assert diag["metadata_cache_misses"] == 18 * 6
        assert diag["metadata_cache_size"] == 18 * 6

        # metadata object is decoupled from the field object
        md = ds[0].metadata()
        assert not hasattr(md, "_field")
        assert ds[0].handle != md._handle


def test_grib_cache_2():
    with settings.temporary(
        {"grib-field-cache": True, "grib-handle-cache-size": 0, "grib-metadata-cache": True}
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert len(ds._field_cache) == 18
        assert ds._handle_cache is None

        diag = ds._diag()
        ref = {
            "handle_count": 18,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }

        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        for i, f in enumerate(ds):
            assert i in ds._field_cache, f"{i} not in cache"
            assert id(f) == id(ds._field_cache[i]), f"{i} not the same object"

        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        # metadata object is decoupled from the field object
        md = ds[0].metadata()
        assert not hasattr(md, "_field")
        assert ds[0]._handle != md._handle
