#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import json
import pickle

import eccodes
import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.field import Field
from earthkit.data.field.grib.context import GribIndexerContext
from earthkit.data.field.grib.geography import create_geography_from_index
from earthkit.data.readers.grib.handle import FileGribHandle
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file

_STORABLE_TYPES = (type(None), int, float, str, bool, list, dict)


def _plain_field_and_handle(path):
    """Return the plain field of the first message and a lazy handle for the same message."""
    ds = from_source("file", path).to_fieldlist()
    field = ds[0]
    handle = FileGribHandle.from_part(ds.part(0), "persistent")
    return field, handle


def _index_dict(field):
    """Return the flat indexer dict of a field, round-tripped through json types."""
    ctx = GribIndexerContext()
    field._get_grib_context(ctx)
    # the storage also keeps datetime etc. for the other components, here only the
    # geography keys are of interest and they must be json-compatible
    d = {k: v for k, v in ctx.items() if k.startswith("geography.")}
    return json.loads(json.dumps(d))


@pytest.fixture
def handle_counter(monkeypatch):
    """Count the eccodes handles created from files."""
    counter = {"n": 0}
    orig = eccodes.codes_new_from_file

    def _new_from_file(*args, **kwargs):
        counter["n"] += 1
        return orig(*args, **kwargs)

    monkeypatch.setattr(eccodes, "codes_new_from_file", _new_from_file)
    return counter


_FILES = {
    "ll": earthkit_examples_file("tuv_pl.grib"),
    "ll_10_20": earthkit_test_data_file("ll_10_20.grib"),
    "o32": earthkit_test_data_file("O32_global.grib2"),
    "mercator": earthkit_test_data_file("mercator.grib"),
}


def _check_geography(field, handle, d, counter, lat_lon_handles):
    ref = field.geography
    shape = ref.shape()
    uid = ref.unique_grid_id()
    lat = ref.latitudes()
    lon = ref.longitudes()

    counter["n"] = 0
    f = Field._from_flat_dict(d, handle)
    geo = f.geography

    assert geo.shape() == shape
    assert f.shape == shape
    assert geo.unique_grid_id() == uid
    assert counter["n"] == 0

    v = geo.latitudes()
    assert v.shape == lat.shape
    assert np.allclose(v, lat)
    v = geo.longitudes()
    assert v.shape == lon.shape
    assert np.allclose(v, lon)

    if lat_lon_handles == 0:
        assert counter["n"] == 0
    else:
        assert counter["n"] >= lat_lon_handles

    # still the same after lat/lon was requested
    assert geo.shape() == shape
    assert geo.unique_grid_id() == uid
    return f


@pytest.mark.parametrize("name", ["ll", "ll_10_20"])
def test_grib_index_geography_regular_ll(name, handle_counter):
    field, handle = _plain_field_and_handle(_FILES[name])
    d = _index_dict(field)

    assert isinstance(d["geography.shape"], list)
    assert all(isinstance(x, int) for x in d["geography.shape"])
    assert tuple(d["geography.shape"]) == field.geography.shape()
    assert d["geography.unique_grid_id"] == field.geography.unique_grid_id()
    assert isinstance(d["geography.grid_spec"], str)
    assert all(isinstance(v, _STORABLE_TYPES) for v in d.values())

    handle_counter["n"] = 0
    _check_geography(field, handle, d, handle_counter, 0)
    assert handle_counter["n"] == 0
    assert handle._handle is None


def test_grib_index_geography_o32(handle_counter):
    field, handle = _plain_field_and_handle(_FILES["o32"])
    d = _index_dict(field)

    assert isinstance(d["geography.grid_spec"], str)
    assert len(d["geography.shape"]) == 1

    handle_counter["n"] = 0
    f = _check_geography(field, handle, d, handle_counter, 0)
    assert handle_counter["n"] == 0
    assert handle._handle is None

    # other keys come from the grid spec
    assert f.geography.grid_spec() == field.geography.grid_spec()
    assert f.geography.grid_type() == field.geography.grid_type()


def test_grib_index_geography_mercator(handle_counter):
    field, handle = _plain_field_and_handle(_FILES["mercator"])
    d = _index_dict(field)

    assert "geography.grid_spec" not in d
    assert isinstance(d["geography.shape"], list)
    assert isinstance(d["geography.unique_grid_id"], str)
    assert all(isinstance(v, _STORABLE_TYPES) for v in d.values())

    ref = field.geography
    shape = ref.shape()
    uid = ref.unique_grid_id()
    lat = ref.latitudes()
    lon = ref.longitudes()

    handle_counter["n"] = 0
    f = Field._from_flat_dict(d, handle)
    geo = f.geography

    assert geo.shape() == shape
    assert f.shape == shape
    assert geo.unique_grid_id() == uid
    assert handle_counter["n"] == 0
    assert handle._handle is None

    assert np.allclose(geo.latitudes(), lat)
    assert handle_counter["n"] >= 1
    assert np.allclose(geo.longitudes(), lon)
    assert geo.grid_type() == ref.grid_type()
    assert geo.shape() == shape
    assert geo.unique_grid_id() == uid


def test_grib_index_geography_mercator_all_keys(handle_counter):
    # all the checks in one go, with a fresh handle counter
    field, handle = _plain_field_and_handle(_FILES["mercator"])
    d = _index_dict(field)
    _check_geography(field, handle, d, handle_counter, 1)


def test_grib_index_geography_factory_no_handle():
    field, _ = _plain_field_and_handle(_FILES["mercator"])
    d = _index_dict(field)

    # without a handle the shape and unique id are still available
    f = Field._from_flat_dict(d)
    assert f.geography.shape() == field.geography.shape()
    assert f.geography.unique_grid_id() == field.geography.unique_grid_id()


def test_grib_index_geography_factory_empty():
    assert create_geography_from_index({}) is None
    assert create_geography_from_index({"grid_spec": None, "shape": None, "unique_grid_id": None}) is None


def test_grib_index_geography_lazy_pickle(handle_counter):
    field, handle = _plain_field_and_handle(_FILES["mercator"])
    d = _index_dict(field)
    f = Field._from_flat_dict(d, handle)

    geo = pickle.loads(pickle.dumps(f.geography))
    assert geo.shape() == field.geography.shape()
    assert geo.unique_grid_id() == field.geography.unique_grid_id()
    assert np.allclose(geo.latitudes(), field.geography.latitudes())
