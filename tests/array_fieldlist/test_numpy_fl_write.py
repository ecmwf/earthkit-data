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
import sys

import numpy as np
import pytest

from earthkit.data import FieldList
from earthkit.data import create_target
from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import ARRAY_BACKENDS
from earthkit.data.testing import check_array_type
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from array_fl_fixtures import load_array_fl  # noqa: E402

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
def test_array_fl_grib_write_to_path(array_backend):

    array_namespace, device, dtype = array_backend

    ds = from_source("file", earthkit_examples_file("test.grib"))
    ds = ds.to_fieldlist(
        array_namespace=array_namespace,
        device=device,
        dtype=dtype,
    )

    assert ds[0].get("parameter.variable") == "2t"
    assert ds[0].get("metadata.shortName") == "2t"
    assert len(ds) == 2
    v1 = ds[0].values + 1
    check_array_type(v1, array_namespace)

    r = ds[0].set({"values": v1, "parameter.variable": "msl"})

    with temp_file() as tmp:
        r.to_target("file", tmp)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        r_tmp = r_tmp.to_fieldlist(array_namespace=array_namespace, device=device, dtype=dtype)
        v_tmp = r_tmp[0].values
        assert array_namespace.allclose(v1, v_tmp)


@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("_kwargs", [{}, {"check_nans": True}])
def test_array_fl_grib_write_missing(array_backend, _kwargs):

    array_namespace, device, dtype = array_backend
    xp = array_namespace

    ds = from_source("file", earthkit_examples_file("test.grib"))
    ds = ds.to_fieldlist(array_namespace=array_namespace, device=device, dtype=dtype)

    assert ds[0].get("metadata.shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    assert not xp.isnan(v1[0])
    assert not xp.isnan(v1[1])
    v1[0] = xp.nan
    assert xp.isnan(v1[0])
    assert not xp.isnan(v1[1])

    # md = ds[0].metadata()
    # md1 = md.override(shortName="msl")
    # r = FieldList.from_array(v1, md1)
    r = ds[0].set({"values": v1, "parameter.variable": "msl"})
    r = FieldList.from_fields([r])

    assert xp.isnan(r[0].values[0])
    assert not xp.isnan(r[0].values[1])

    with temp_file() as tmp:
        r.to_target("file", tmp, **_kwargs)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        v_tmp = r_tmp[0].values
        assert np.isnan(v_tmp[0])
        r_tmp = r_tmp.to_fieldlist(array_namespace=array_namespace, device=device, dtype=dtype)
        v_tmp = r_tmp[0].values
        assert xp.isnan(v_tmp[0])
        assert not xp.isnan(v_tmp[1])


def test_array_fl_grib_write_check_nans_bad():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].get("metadata.shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    assert not np.isnan(v1[0])
    assert not np.isnan(v1[1])
    v1[0] = np.nan
    assert np.isnan(v1[0])
    assert not np.isnan(v1[1])

    # md = ds[0].metadata()
    # md1 = md.override(shortName="msl")
    # r = FieldList.from_numpy(v1, md1)
    r = ds[0].set({"values": v1, "parameter.variable": "msl"})
    r = FieldList.from_fields([r])

    assert np.isnan(r[0].values[0])
    assert not np.isnan(r[0].values[1])

    with temp_file() as tmp:
        from eccodes import EncodingError

        with pytest.raises(EncodingError):
            r.to_target("file", tmp, check_nans=False)


def test_array_fl_grib_write_append():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].get("metadata.shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    v2 = v + 2

    r1 = ds[0].set({"values": v1, "parameter.variable": "msl"})
    r1 = FieldList.from_fields([r1])

    r2 = ds[0].set({"values": v2, "parameter.variable": "2d"})
    r2 = FieldList.from_fields([r2])

    # save to disk
    tmp = temp_file()
    r1.to_target("file", tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 1
    assert r_tmp.get("metadata.shortName") == ["msl"]
    r_tmp = None

    # append
    r2.to_target("file", tmp.path, append=True)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 2
    assert r_tmp.get("metadata.shortName") == ["msl", "2d"]


def test_array_fl_grib_write_generating_proc_id():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].get("metadata.shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    v2 = v + 2

    f1 = ds[0].set({"values": v1, "parameter.variable": "msl"})
    f2 = ds[0].set({"values": v2, "parameter.variable": "2d"})
    r1 = FieldList.from_fields([f1, f2])

    # save to disk
    with temp_file() as tmp:
        with create_target("file", tmp) as t:
            t.write(r1[0], metadata={"generatingProcessIdentifier": 255})
            t.write(r1[1])

        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        assert len(r_tmp) == 2
        assert r_tmp.get("metadata.shortName") == ["msl", "2d"]
        assert r_tmp.get("metadata.generatingProcessIdentifier") == [
            255,
            150,
        ]

        assert np.allclose(r_tmp.values[0], v1)
        assert np.allclose(r_tmp.values[1], v2)


@pytest.mark.migrate
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize(
    "_kwargs,expected_value",
    [({}, None), ({"bits_per_value": 12}, 12), ({"bits_per_value": None}, None)],
)
def test_array_fl_grib_write_bits_per_value(array_backend, _kwargs, expected_value):
    ds, _ = load_array_fl(1, array_backend)

    if expected_value is None:
        expected_value = ds[0].get("metadata.bitsPerValue")

    with temp_file() as tmp:
        ds.to_target("file", tmp, **_kwargs)
        ds1 = from_source("file", tmp)
        assert ds1.get("metadata.bitsPerValue") == [expected_value] * len(ds)


@pytest.mark.parametrize(
    "filename,shape",
    [
        (earthkit_examples_file("test.grib"), (11, 19)),
        (earthkit_test_data_file("O32_global.grib1"), (5248,)),
        (earthkit_test_data_file("O32_global.grib2"), (5248,)),
    ],
)
def test_array_fl_grib_single_write_to_path(filename, shape):
    ds = from_source("file", filename)

    assert len(ds) >= 1
    v1 = ds[0].values + 1

    r = ds[0].set({"values": v1, "parameter.variable": "msl"})
    r = FieldList.from_fields([r])

    assert r[0].shape == shape

    with temp_file() as tmp:
        r.to_target("file", tmp)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        # r_tmp = r_tmp.to_fieldlist(array_namespace=array_namespace)
        assert r_tmp[0].shape == shape
        assert r_tmp[0].get("metadata.shortName") == "msl"
        v_tmp = r_tmp[0].values
        assert np.allclose(v1, v_tmp)


@pytest.mark.migrate
@pytest.mark.parametrize(
    "filename,shape",
    [
        (earthkit_examples_file("test.grib"), (11, 19)),
        (earthkit_test_data_file("O32_global.grib1"), (5248,)),
        (earthkit_test_data_file("O32_global.grib2"), (5248,)),
    ],
)
@pytest.mark.parametrize(
    "_kwargs,expected_value",
    [({}, None), ({"bits_per_value": 8}, 8), ({"bits_per_value": None}, None)],
)
def test_array_fl_grib_single_write_bits_per_value(filename, shape, _kwargs, expected_value):
    ds0 = from_source("file", filename)

    # ds = ds0.from_fields([ds0[0].copy()])
    ds = ds0.to_fieldlist()
    assert ds[0].shape == shape

    if expected_value is None:
        expected_value = ds[0].get("metadata.bitsPerValue")

    with temp_file() as tmp:
        ds.to_target("file", tmp, **_kwargs)
        ds1 = from_source("file", tmp)
        assert ds1.get("metadata.bitsPerValue") == [expected_value] * len(ds)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
