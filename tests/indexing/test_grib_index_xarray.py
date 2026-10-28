#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""``to_fieldlist(index=...).to_xarray()`` against the plain GRIB path.

The indexed Xarray dataset must be identical to the plain one and GRIB data
must be read only when the values are loaded.
"""

import numpy as np
import pytest
import xarray as xr
from indexing_fixtures import install_handle_counter  # noqa: E402

from earthkit.data import config, from_source
from earthkit.data.readers.grib.index import GribIndex
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file

PROFILES = [None, "grib"]

# name -> (list of files, number of fields, number of data variables)
SOURCES = {
    "tuv_pl": ([earthkit_examples_file("tuv_pl.grib")], 18, 3),
    "multi": (
        [earthkit_test_data_file(f"{x}_pl.grib") for x in ["t", "u", "v"]],
        18,
        3,
    ),
    "ens_50": ([earthkit_test_data_file("ens_50.grib")], None, None),
    "O32": ([earthkit_test_data_file("O32_global.grib2")], None, None),
    "t_time_series": ([earthkit_test_data_file("t_time_series.grib")], None, None),
}


def _source(paths):
    return from_source("file", paths if len(paths) > 1 else paths[0])


def _indexed(paths, db_path):
    """Build the index first (it scans the files), then return a fieldlist
    built from the existing db.
    """
    GribIndex.open(paths, db_path=db_path).close()
    return _source(paths).to_fieldlist(index=db_path)


def _profile_kwargs(profile):
    return {} if profile is None else {"profile": profile}


def _assert_same(ds, plain, source_name):
    """Assert that the two datasets are identical.

    Documented difference: for the reduced Gaussian grid (O32) the indexed
    fields have a gridSpec based geography (no GRIB handle), so the lat/lon
    values come from eckit instead of eccodes and differ by rounding errors
    (~1e-14 degrees). They are compared with a tight absolute tolerance and
    everything else must be identical.
    """
    if source_name == "O32":
        for k in ["latitude", "longitude"]:
            assert ds[k].dims == plain[k].dims
            assert ds[k].attrs == plain[k].attrs
            np.testing.assert_allclose(ds[k].values, plain[k].values, rtol=0, atol=1e-10)
        ds = ds.drop_vars(["latitude", "longitude"])
        plain = plain.drop_vars(["latitude", "longitude"])
    xr.testing.assert_identical(ds, plain)


@pytest.fixture(params=list(SOURCES))
def source_name(request):
    return request.param


@pytest.fixture(params=PROFILES, ids=["default", "grib"])
def profile(request):
    return request.param


def _paths(source_name):
    return SOURCES[source_name][0]


@pytest.mark.parametrize("add_attrs", [False, True], ids=["no_attrs", "attrs"])
def test_grib_index_xarray_identical_and_lazy(tmp_path, monkeypatch, source_name, profile, add_attrs):
    paths = _paths(source_name)
    kwargs = _profile_kwargs(profile)
    kwargs["add_earthkit_attrs"] = add_attrs

    plain = _source(paths).to_fieldlist().to_xarray(**kwargs)

    # the db is built before the counter is installed
    db_path = str(tmp_path / "idx.sqlite")
    ds_index = _indexed(paths, db_path)
    nfields = len(ds_index)

    counter = install_handle_counter(monkeypatch)
    ds = ds_index.to_xarray(**kwargs)
    n_build = counter["n"]
    nvars = len(ds.data_vars)

    # building the dataset
    if add_attrs:
        # one header message per data variable at most
        assert n_build <= nvars
    else:
        assert n_build == 0

    # loading the values: at most one handle per field plus the attrs allowance
    ds.load()
    n_load = counter["n"] - n_build
    assert n_load <= nfields
    if not add_attrs:
        # nothing was read before
        assert n_load > 0

    if add_attrs:
        # the earthkit attrs hold the base64 encoded message, which is not part
        # of the comparison below, so check that it is there and equal
        for v in ds.data_vars:
            assert ds[v].attrs["_earthkit"] == plain[v].attrs["_earthkit"]

    _assert_same(ds, plain, source_name)


def test_grib_index_xarray_nfields_vars():
    # keep the test table honest
    for name in ["tuv_pl", "multi"]:
        paths, nfields, nvars = SOURCES[name]
        ds = _source(paths).to_fieldlist()
        assert len(ds) == nfields
        assert len(ds.to_xarray().data_vars) == nvars


def test_grib_index_xarray_values_equal_plain(tmp_path, source_name):
    paths = _paths(source_name)
    plain = _source(paths).to_fieldlist().to_xarray(add_earthkit_attrs=False)
    ds = _indexed(paths, str(tmp_path / "idx.sqlite")).to_xarray(add_earthkit_attrs=False)

    assert set(ds.data_vars) == set(plain.data_vars)
    for v in plain.data_vars:
        assert ds[v].dims == plain[v].dims
        assert ds[v].shape == plain[v].shape
        assert (ds[v].values == plain[v].values).all()


def test_grib_index_xarray_default_attrs_message(tmp_path, monkeypatch):
    """The default earthkit attrs read one header message per variable."""
    paths = _paths("tuv_pl")
    plain = _source(paths).to_fieldlist().to_xarray()
    ds_index = _indexed(paths, str(tmp_path / "idx.sqlite"))

    counter = install_handle_counter(monkeypatch)
    ds = ds_index.to_xarray()
    assert 0 < counter["n"] <= len(ds.data_vars)
    xr.testing.assert_identical(ds.load(), plain)


def test_grib_index_xarray_index_true_cache(tmp_path, monkeypatch):
    """``index=True`` (one db per file in the user cache) behaves the same."""
    paths = _paths("multi")
    plain = _source(paths).to_fieldlist().to_xarray(add_earthkit_attrs=False)

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    with config.temporary({"cache-policy": "user", "user-cache-directory": str(cache_dir)}):
        _source(paths).to_fieldlist(index=True)
        fl = _source(paths).to_fieldlist(index=True)

        counter = install_handle_counter(monkeypatch)
        ds = fl.to_xarray(add_earthkit_attrs=False)
        assert counter["n"] == 0
        ds.load()
        assert counter["n"] <= len(fl)
        xr.testing.assert_identical(ds, plain)


MERCATOR = earthkit_test_data_file("mercator.grib")


def test_grib_index_xarray_mercator_no_attrs(tmp_path, monkeypatch):
    """Grids without a gridSpec need the GRIB handle for the lat/lon of the
    first field, so before ``.load()`` at most one handle per distinct grid
    (here: one) is allowed. The values need at most one handle per field.
    """
    plain = _source([MERCATOR]).to_fieldlist().to_xarray(add_earthkit_attrs=False)

    ds_index = _indexed([MERCATOR], str(tmp_path / "idx.sqlite"))
    nfields = len(ds_index)
    ngrids = len(set(ds_index.get("geography.unique_grid_id")))
    assert ngrids == 1

    counter = install_handle_counter(monkeypatch)
    ds = ds_index.to_xarray(add_earthkit_attrs=False)
    n_build = counter["n"]
    assert n_build <= ngrids

    ds.load()
    assert counter["n"] - n_build <= nfields
    xr.testing.assert_identical(ds, plain)


def test_grib_index_xarray_mercator_attrs(tmp_path, monkeypatch):
    """The earthkit attrs allow one more handle per data variable."""
    plain = _source([MERCATOR]).to_fieldlist().to_xarray()

    ds_index = _indexed([MERCATOR], str(tmp_path / "idx.sqlite"))
    counter = install_handle_counter(monkeypatch)
    ds = ds_index.to_xarray()
    ngrids = 1
    assert counter["n"] <= ngrids + len(ds.data_vars)
    xr.testing.assert_identical(ds.load(), plain)


def test_grib_index_xarray_dask(tmp_path, monkeypatch):
    pytest.importorskip("dask")

    paths = _paths("tuv_pl")
    kwargs = dict(add_earthkit_attrs=False, chunks={"level": 1})

    plain = _source(paths).to_fieldlist().to_xarray(**kwargs)
    ds_index = _indexed(paths, str(tmp_path / "idx.sqlite"))

    counter = install_handle_counter(monkeypatch)
    ds = ds_index.to_xarray(**kwargs)
    assert counter["n"] == 0
    assert ds["t"].chunks[0] == (1,) * 6

    ds = ds.compute()
    assert 0 < counter["n"] <= len(ds_index)
    xr.testing.assert_identical(ds, plain.compute())
