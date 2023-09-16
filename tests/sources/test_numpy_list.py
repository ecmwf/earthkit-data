#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file

LOG = logging.getLogger(__name__)


def _check_save_to_disk(ds, len_ref, meta_ref):
    tmp = temp_file()
    ds.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == len_ref
    assert r_tmp.metadata("shortName") == meta_ref
    r_tmp = None


def _prepare_ds(num):
    assert num in [1, 2, 3]
    files = ["test.grib", "test6.grib", "tuv_pl.grib"]
    files = files[:num]

    ds_in = []
    md = []
    for fname in files:
        ds_in.append(from_source("file", earthkit_examples_file(fname)))
        md += ds_in[-1].metadata("param")

    ds = []
    for x in ds_in:
        ds.append(
            FieldList.from_numpy(
                x.values, [m.override(edition=1) for m in x.metadata()]
            )
        )

    return (*ds, md)


def test_numpy_list_grib_single_field():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    lat, lon, v = ds[0].data(flatten=True)
    v1 = v + 1

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    r = FieldList.from_numpy(v1, md1)

    def _check_field(r):
        assert len(r) == 1
        assert np.allclose(r[0].values, v1)
        assert r[0].shape == ds[0].shape
        assert r[0].metadata("shortName") == "msl"
        _lat, _lon, _v = r[0].data(flatten=True)
        assert np.allclose(_lat, lat)
        assert np.allclose(_lon, lon)
        assert np.allclose(_v, v1)

    _check_field(r)

    # save to disk
    tmp = temp_file()
    r.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    _check_field(r_tmp)


def test_numpy_list_grib_multi_field():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    v = ds.values
    v1 = v + 1

    md1 = [f.metadata().override(shortName="2d") for f in ds]
    r = FieldList.from_numpy(v1, md1)

    assert len(r) == 2
    assert np.allclose(v1, r.values)
    for i, f in enumerate(r):
        assert f.shape == ds[i].shape
        assert f.metadata("shortName") == "2d", f"shortName {i}"
        assert f.metadata("name") == "2 metre dewpoint temperature", f"name {i}"

    # save to disk
    tmp = temp_file()
    r.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 2
    assert np.allclose(v1, r_tmp.values)
    for i, f in enumerate(r_tmp):
        assert f.shape == ds[i].shape
        assert f.metadata("shortName") == "2d", f"shortName {i}"
        assert f.metadata("name") == "2 metre dewpoint temperature", f"name {i}"


def test_numpy_list_grib_write_missing():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    assert not np.isnan(v1[0])
    assert not np.isnan(v1[1])
    v1[0] = np.nan
    assert np.isnan(v1[0])
    assert not np.isnan(v1[1])

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    r = FieldList.from_numpy(v1, md1)

    assert np.isnan(r[0].values[0])
    assert not np.isnan(r[0].values[1])

    # save to disk
    tmp = temp_file()
    r.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    v_tmp = r_tmp[0].values
    assert np.isnan(v_tmp[0])
    assert not np.isnan(v_tmp[1])


def test_numpy_list_grib_write_append():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    v2 = v + 2

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    md2 = md.override(shortName="2d")

    r1 = FieldList.from_numpy(v1, md1)
    r2 = FieldList.from_numpy(v2, md2)

    # save to disk
    tmp = temp_file()
    r1.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 1
    assert r_tmp.metadata("shortName") == ["msl"]
    r_tmp = None

    # append
    r2.save(tmp.path, append=True)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 2
    assert r_tmp.metadata("shortName") == ["msl", "2d"]


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_numpy_list_grib_concat_2a(mode):
    ds1, ds2, md = _prepare_ds(2)

    if mode == "oper":
        ds = ds1 + ds2
    else:
        ds = from_source("multi", ds1, ds2)

    assert len(ds) == 8
    assert ds.metadata("param") == md

    f1 = ds.sel(shortName="msl")
    assert len(f1) == 1
    assert f1.metadata("shortName") == ["msl"]
    assert np.allclose(f1[0].values, ds1[1].values)

    _check_save_to_disk(ds, 8, md)


def test_numpy_list_grib_concat_2b():
    ds1, ds2, md = _prepare_ds(2)
    ds1 += ds2

    assert len(ds1) == 8
    assert ds1.metadata("param") == md

    f1 = ds1.sel(shortName="msl")
    assert len(f1) == 1
    assert f1.metadata("shortName") == ["msl"]
    assert np.allclose(f1[0].values, ds1[1].values)

    _check_save_to_disk(ds1, 8, md)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_numpy_list_grib_concat_3a(mode):
    ds1, ds2, ds3, md = _prepare_ds(3)

    if mode == "oper":
        ds = ds1 + ds2
        ds = ds + ds3
    else:
        ds = from_source("multi", ds1, ds2)
        ds = from_source("multi", ds, ds3)

    assert len(ds) == 26
    assert ds.metadata("param") == md
    _check_save_to_disk(ds, 26, md)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_numpy_list_grib_concat_3b(mode):
    ds1, ds2, ds3, md = _prepare_ds(3)

    if mode == "oper":
        ds = ds1 + ds2 + ds3
    else:
        ds = from_source("multi", ds1, ds2, ds3)

    assert len(ds) == 26
    assert ds.metadata("param") == md
    _check_save_to_disk(ds, 26, md)


def test_numpy_list_grib_from_empty_1():
    ds_e = FieldList()
    ds, md = _prepare_ds(1)
    ds1 = ds_e + ds
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    assert ds1.metadata("param") == md
    _check_save_to_disk(ds1, 2, md)


def test_numpy_list_grib_from_empty_2():
    ds_e = FieldList()
    ds, md = _prepare_ds(1)
    ds1 = ds + ds_e
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    assert ds1.metadata("param") == md
    _check_save_to_disk(ds1, 2, md)


def test_numpy_list_grib_from_empty_3():
    ds_e = FieldList()
    ds1, ds2, md = _prepare_ds(2)
    ds = ds_e + ds1 + ds2
    assert len(ds) == 8
    assert ds.metadata("param") == md
    _check_save_to_disk(ds, 8, md)


def test_numpy_list_grib_from_empty_4():
    ds = FieldList()
    ds1, md = _prepare_ds(1)
    ds += ds1
    assert id(ds) == id(ds1)
    assert len(ds) == 2
    assert ds.metadata("param") == md
    _check_save_to_disk(ds, 2, md)


def test_numpy_list_grib_from_empty_5():
    ds = FieldList()
    ds1, ds2, md = _prepare_ds(2)
    ds += ds1 + ds2
    assert len(ds) == 8
    assert ds.metadata("param") == md
    _check_save_to_disk(ds, 8, md)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
