#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import eccodes
import numpy as np
import pytest
from earthkit.utils.array import convert as array_convert
from earthkit.utils.array.convert import convert_dtype
from grib_fixtures import (
    FL_FILE,  # noqa: E402
    FL_NUMPY,  # noqa: E402
    FL_TYPES,  # noqa: E402
    load_grib_data,  # noqa: E402
)

from earthkit.data import create_encoder, from_source
from earthkit.data.utils.testing import check_array, check_array_type, earthkit_examples_file


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_values_1(fl_type):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    xp = array_backend.array_namespace
    eps = 1e-5

    dtype = "float64"
    if array_backend.dtype is not None:
        dtype = array_backend.dtype

    # whole file
    v = f.values
    check_array_type(v, xp, dtype=dtype)
    assert v.shape == (1, 84)
    v = v[0].flatten()
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )

    # field
    v1 = f[0].values

    check_array_type(v1, xp, dtype=dtype)
    assert v1.shape == (84,)
    assert xp.allclose(v, v1, rtol=eps)


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_values_18(fl_type):
    f, array_backend = load_grib_data("tuv_pl.grib", fl_type)
    xp = array_backend.array_namespace
    eps = 1e-5

    dtype = "float64"
    if array_backend.dtype is not None:
        dtype = array_backend.dtype

    # whole file
    v = f.values
    check_array_type(v, xp, dtype=dtype)
    assert v.shape == (18, 84)
    vf = v[0].flatten()
    check_array(
        vf,
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    vf = v[15].flatten()
    check_array(
        vf,
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_to_numpy_1(fl_type):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    dtype = np.float64
    if array_backend.dtype is not None:
        dtype = convert_dtype(array_backend.dtype, "numpy")

    print(f"dtype: {dtype}")
    eps = 1e-5
    v = f.to_numpy()
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    v = v[0].flatten()
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "first,options, expected_shape",
    [
        (False, {}, (1, 7, 12)),
        (False, {"flatten": True}, (1, 84)),
        (False, {"flatten": False}, (1, 7, 12)),
        (True, {}, (7, 12)),
        (True, {"flatten": True}, (84,)),
        (True, {"flatten": False}, (7, 12)),
    ],
)
def test_grib_to_numpy_1_shape(fl_type, first, options, expected_shape):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    dtype = np.float64
    if array_backend.dtype is not None:
        dtype = dtype = convert_dtype(array_backend.dtype, "numpy")

    v_ref = f[0].to_numpy().flatten()
    eps = 1e-5

    data = f[0] if first else f
    v1 = data.to_numpy(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.dtype == dtype
    assert v1.shape == expected_shape
    v1 = v1.flatten()
    assert np.allclose(v_ref, v1, eps)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_to_numpy_18(fl_type):
    f, array_backend = load_grib_data("tuv_pl.grib", fl_type)

    dtype = np.float64
    if array_backend.dtype is not None:
        dtype = dtype = convert_dtype(array_backend.dtype, "numpy")

    eps = 1e-5

    # whole file
    v = f.to_numpy(flatten=True)
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    assert v.shape == (18, 84)
    vf0 = v[0].flatten()
    check_array(
        vf0,
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    vf15 = v[15].flatten()
    check_array(
        vf15,
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "options, expected_shape",
    [
        (
            {},
            (
                18,
                7,
                12,
            ),
        ),
        (
            {"flatten": True},
            (
                18,
                84,
            ),
        ),
        ({"flatten": False}, (18, 7, 12)),
    ],
)
def test_grib_to_numpy_18_shape(fl_type, options, expected_shape):
    f, array_backend = load_grib_data("tuv_pl.grib", fl_type)

    dtype = np.float64
    if array_backend.dtype is not None:
        dtype = dtype = convert_dtype(array_backend.dtype, "numpy")

    eps = 1e-5

    # whole file
    v = f.to_numpy()
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    assert v.shape == (18, 7, 12)
    vf0 = f[0].to_numpy().flatten()
    assert vf0.shape == (84,)
    vf15 = f[15].to_numpy().flatten()
    assert vf15.shape == (84,)

    v1 = f.to_numpy(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.dtype == dtype
    assert v1.shape == expected_shape
    vr = v1[0].flatten()
    assert np.allclose(vf0, vr, eps)
    vr = v1[15].flatten()
    assert np.allclose(vf15, vr, eps)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_numpy_1_dtype(fl_type, dtype):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    v = f[0].to_numpy(dtype=dtype)
    assert v.dtype == dtype

    v = f.to_numpy(dtype=dtype)
    assert v.dtype == dtype


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_numpy_18_dtype(fl_type, dtype):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    v = f[0].to_numpy(dtype=dtype)
    assert v.dtype == dtype

    v = f.to_numpy(dtype=dtype)
    assert v.dtype == dtype


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_to_numpy_1_index(fl_type):
    ds, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    dtype = np.float64
    if array_backend.dtype is not None:
        dtype = dtype = convert_dtype(array_backend.dtype, "numpy")

    eps = 1e-5

    v = ds[0].to_numpy(flatten=True, index=[0, -1])
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    assert v.shape == (2,)
    assert np.allclose(v, [260.43560791015625, 227.18560791015625])

    v = ds[0].to_numpy(flatten=True, index=slice(None, None))
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )

    v = ds[0].to_numpy(index=(slice(None, 2), slice(None, 3)))
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    assert v.shape == (2, 3)
    assert np.allclose(
        v,
        [
            [260.43560791, 260.43560791, 260.43560791],
            [280.81060791, 277.06060791, 284.43560791],
        ],
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_to_numpy_18_index(fl_type):
    ds, array_backend = load_grib_data("tuv_pl.grib", fl_type)

    dtype = np.float64
    if array_backend.dtype is not None:
        dtype = convert_dtype(array_backend.dtype, "numpy")

    eps = 1e-5

    v = ds.to_numpy(flatten=True, index=[0, -1])
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    assert v.shape == (18, 2)
    vf0 = v[0].flatten()
    assert np.allclose(vf0, [272.5642, 240.56417846679688])
    vf15 = v[15].flatten()
    assert np.allclose(vf15, [226.6531524658203, 206.6531524658203])

    v = ds.to_numpy(flatten=True, index=slice(None, 2))
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    assert v.shape == (18, 2)
    vf0 = v[0].flatten()
    assert np.allclose(vf0, [272.56417847, 272.56417847])
    vf15 = v[15].flatten()
    assert np.allclose(vf15, [226.65315247, 226.65315247])

    v = ds.to_numpy(flatten=True, index=slice(None, None))
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    assert v.shape == (18, 84)
    vf0 = v[0].flatten()
    check_array(
        vf0,
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    vf15 = v[15].flatten()
    check_array(
        vf15,
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )

    v = ds.to_numpy(index=(slice(None, 2), slice(None, 3)))
    assert isinstance(v, np.ndarray)
    assert v.dtype == dtype
    assert v.shape == (18, 2, 3)
    vf0 = v[0].flatten()
    assert np.allclose(
        vf0,
        [
            272.56417847,
            272.56417847,
            272.56417847,
            288.56417847,
            296.56417847,
            288.56417847,
        ],
    )
    vf15 = v[15].flatten()
    assert np.allclose(
        vf15,
        [
            226.65315247,
            226.65315247,
            226.65315247,
            230.65315247,
            230.65315247,
            230.65315247,
        ],
    )


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("_kwargs", [{}, {"array_namespace": "numpy"}])
def test_grib_to_array_1(fl_type, _kwargs):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    eps = 1e-5
    v = f.to_array(**_kwargs)
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    v = v[0].flatten()
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize(
    "first,options, expected_shape",
    [
        (False, {}, (1, 7, 12)),
        (False, {"flatten": True}, (1, 84)),
        (False, {"flatten": False}, (1, 7, 12)),
        (True, {}, (7, 12)),
        (True, {"flatten": True}, (84,)),
        (True, {"flatten": False}, (7, 12)),
    ],
)
def test_grib_to_array_1_shape(fl_type, first, options, expected_shape):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    v_ref = f[0].to_array().flatten()
    eps = 1e-5

    data = f[0] if first else f
    v1 = data.to_array(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.dtype == np.float64
    assert v1.shape == expected_shape
    v1 = v1.flatten()
    assert np.allclose(v_ref, v1, eps)


@pytest.mark.parametrize("fl_type", FL_FILE)
# @pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize(
    "kwarg,expected_shape,expected_dtype",
    [
        ({}, (8, 13), np.float64),
        ({"flatten": True}, (104,), np.float64),
        ({"flatten": True, "dtype": np.float32}, (104,), np.float32),
        ({"flatten": True, "dtype": np.float64}, (104,), np.float64),
        ({"flatten": False}, (8, 13), np.float64),
        ({"flatten": False, "dtype": np.float32}, (8, 13), np.float32),
        ({"flatten": False, "dtype": np.float64}, (8, 13), np.float64),
    ],
)
def test_grib_field_data(fl_type, kwarg, expected_shape, expected_dtype):
    ds, _ = load_grib_data("test.grib", fl_type)

    lat, lon = ds[0].geography.latlons(**kwarg)
    v = ds[0].to_numpy(**kwarg)

    d = ds[0].data(**kwarg)
    assert isinstance(d, np.ndarray)
    assert d.dtype == expected_dtype
    assert len(d) == 3
    assert d[0].shape == expected_shape
    assert np.allclose(d[0], lat)
    assert np.allclose(d[1], lon)
    assert np.allclose(d[2], v)

    d = ds[0].data(keys="lat", **kwarg)
    assert d.shape == expected_shape
    assert d.dtype == expected_dtype
    assert np.allclose(d, lat)

    d = ds[0].data(keys="lon", **kwarg)
    assert d.shape == expected_shape
    assert d.dtype == expected_dtype
    assert np.allclose(d, lon)

    d = ds[0].data(keys="value", **kwarg)
    assert d.shape == expected_shape
    assert d.dtype == expected_dtype
    assert np.allclose(d, v)

    d = ds[0].data(keys=("value", "lon"), **kwarg)
    assert isinstance(d, np.ndarray)
    assert d.dtype == expected_dtype
    assert len(d) == 2
    assert np.allclose(d[0], v)
    assert np.allclose(d[1], lon)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize(
    "kwarg,expected_shape,expected_dtype",
    [
        ({}, (8, 13), np.float64),
        ({"flatten": True}, (104,), np.float64),
        ({"flatten": True, "dtype": np.float32}, (104,), np.float32),
        ({"flatten": True, "dtype": np.float64}, (104,), np.float64),
        ({"flatten": False}, (8, 13), np.float64),
        ({"flatten": False, "dtype": np.float32}, (8, 13), np.float32),
        ({"flatten": False, "dtype": np.float64}, (8, 13), np.float64),
    ],
)
def test_grib_fieldlist_data(fl_type, kwarg, expected_shape, expected_dtype):
    ds, _ = load_grib_data("test.grib", fl_type)

    lat, lon = ds.geography.latlons(**kwarg)
    v = ds.to_numpy(**kwarg)

    d = ds.data(**kwarg)
    assert isinstance(d, np.ndarray)
    assert d.shape == tuple([4, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d[0], lat)
    assert np.allclose(d[1], lon)
    assert np.allclose(d[2], v[0])
    assert np.allclose(d[3], v[1])

    d = ds.data(keys="lat", **kwarg)
    assert d.shape == tuple([1, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d[0], lat)

    d = ds.data(keys="lon", **kwarg)
    assert d.shape == tuple([1, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d[0], lon)

    d = ds.data(keys="value", **kwarg)
    assert d.shape == tuple([2, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d, v)

    d = ds.data(keys=("value", "lon"), **kwarg)
    assert isinstance(d, np.ndarray)
    assert d.shape == tuple([3, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d[0], v[0])
    assert np.allclose(d[1], v[1])
    assert np.allclose(d[2], lon)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
def test_grib_fieldlist_data_index(fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    eps = 1e-5

    lat, lon = ds.geography.latlons(flatten=True)

    index = [0, -1]
    v = ds.data(flatten=True, index=index)
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    assert v.shape == (18 + 2, 2)
    assert np.allclose(v[0].flatten(), lat[index])
    assert np.allclose(v[1].flatten(), lon[index])
    vf0 = v[2 + 0].flatten()
    assert np.allclose(vf0, [272.5642, 240.56417846679688])
    vf15 = v[2 + 15].flatten()
    assert np.allclose(vf15, [226.6531524658203, 206.6531524658203])

    index = slice(None, 2)
    v = ds.data(flatten=True, index=index)
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    assert v.shape == (18 + 2, 2)
    assert np.allclose(v[0].flatten(), lat[index])
    assert np.allclose(v[1].flatten(), lon[index])
    vf0 = v[2 + 0].flatten()
    assert np.allclose(vf0, [272.56417847, 272.56417847])
    vf15 = v[2 + 15].flatten()
    assert np.allclose(vf15, [226.65315247, 226.65315247])

    index = slice(None, None)
    v = ds.data(flatten=True, index=index)
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    assert v.shape == (18 + 2, 84)
    assert np.allclose(v[0].flatten(), lat)
    assert np.allclose(v[1].flatten(), lon)
    vf0 = v[2 + 0].flatten()
    check_array(
        vf0,
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    vf15 = v[2 + 15].flatten()
    check_array(
        vf15,
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )

    index = (slice(None, 2), slice(None, 3))
    v = ds.data(index=index)
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    assert v.shape == (2 + 18, 2, 3)
    lat, lon = ds.geography.latlons()
    assert np.allclose(v[0], lat[index])
    assert np.allclose(v[1], lon[index])

    vf0 = v[2 + 0].flatten()
    assert np.allclose(
        vf0,
        [
            272.56417847,
            272.56417847,
            272.56417847,
            288.56417847,
            296.56417847,
            288.56417847,
        ],
    )
    vf15 = v[2 + 15].flatten()
    assert np.allclose(
        vf15,
        [
            226.65315247,
            226.65315247,
            226.65315247,
            230.65315247,
            230.65315247,
            230.65315247,
        ],
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_values_with_missing(fl_type):
    f, array_backend = load_grib_data("test_single_with_missing.grib", fl_type, folder="data")

    xp = array_backend.array_namespace
    dtype = array_backend.dtype

    v = f[0].values
    check_array_type(v, xp, dtype=dtype)
    assert v.shape == (84,)
    eps = 0.001

    assert xp.count_nonzero(xp.isnan(v)) == 38
    mask = xp.asarray([12, 14, 15, 24, 25, 26] + list(range(28, 60)))
    v1 = array_convert(v, array_namespace="numpy")

    assert np.isclose(v1[0], 260.4356, eps)
    assert np.isclose(v1[11], 260.4356, eps)
    assert np.isclose(v1[-1], 227.1856, eps)
    m = v[mask]
    assert len(m) == 38
    assert xp.count_nonzero(xp.isnan(m)) == 38


def _make_complex_missing_message():
    """Build an in-memory GRIB2 message with missing values but no bitmap.

    The message uses complex packing with missing value management
    (``missingValueManagementUsed=1``, ``bitmapPresent=0``). Returns the
    message bytes and the expected values with NaN at the missing points.
    """
    h = eccodes.codes_grib_new_from_samples("GRIB2")
    try:
        eccodes.codes_set(h, "packingType", "grid_complex")
        n = eccodes.codes_get(h, "numberOfValues")
        missing_idx = [0, 5, n // 4, n // 2, n - 1]

        values = np.linspace(200, 300, n)
        values[missing_idx] = 9999  # the missing value stored in the message

        eccodes.codes_set(h, "missingValue", 9999)
        eccodes.codes_set(h, "missingValueManagementUsed", 1)
        eccodes.codes_set(h, "bitmapPresent", 0)
        # set explicitly: with complex packing chosen before the values, the
        # sample's bitsPerValue can stay 0 and the values would be lost
        eccodes.codes_set(h, "bitsPerValue", 16)
        eccodes.codes_set_values(h, values)

        message = eccodes.codes_get_message(h)
    finally:
        eccodes.codes_release(h)

    expected = np.linspace(200, 300, n)
    expected[missing_idx] = np.nan

    return message, expected


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_values_missing_no_bitmap(fl_type, tmp_path):
    message, expected = _make_complex_missing_message()

    # the serialised message stores missing values without a bitmap
    h = eccodes.codes_new_from_message(message)
    try:
        assert eccodes.codes_get(h, "bitmapPresent") == 0
        assert eccodes.codes_get(h, "missingValueManagementUsed") == 1
        assert eccodes.codes_get(h, "numberOfMissing") == np.count_nonzero(np.isnan(expected))
    finally:
        eccodes.codes_release(h)

    path = tmp_path / "test_missing_no_bitmap.grib"
    path.write_bytes(message)

    f, array_backend = load_grib_data(str(path), fl_type, folder="data")

    xp = array_backend.array_namespace
    dtype = array_backend.dtype

    v = f[0].values
    check_array_type(v, xp, dtype=dtype)

    mask_expected = np.isnan(expected)
    assert xp.count_nonzero(xp.isnan(v)) == len(np.flatnonzero(mask_expected))

    v1 = array_convert(v, array_namespace="numpy").flatten()
    assert v1.shape == expected.shape
    assert np.array_equal(np.isnan(v1), mask_expected)
    assert np.allclose(v1[~mask_expected], expected[~mask_expected], atol=0.01)

    # reading with a memory source gives the same result
    fm = from_source("memory", message).to_fieldlist()
    vm = array_convert(fm[0].values, array_namespace="numpy").flatten()
    assert np.array_equal(np.isnan(vm), mask_expected)
    assert np.allclose(vm[~mask_expected], expected[~mask_expected], atol=0.01)

    # also with float32
    v32 = array_convert(f[0].to_numpy(flatten=True, dtype="float32"), array_namespace="numpy")
    assert v32.dtype == np.float32
    assert np.array_equal(np.isnan(v32), mask_expected)
    assert np.allclose(v32[~mask_expected], expected[~mask_expected], atol=0.01)


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_values_missing_no_bitmap_roundtrip(fl_type, tmp_path):
    message, expected = _make_complex_missing_message()

    path = tmp_path / "test_missing_no_bitmap.grib"
    path.write_bytes(message)

    f, array_backend = load_grib_data(str(path), fl_type, folder="data")
    xp = array_backend.array_namespace

    # re-encode the values using the field as template
    v = f[0].values
    mask_expected = np.isnan(expected)
    assert xp.count_nonzero(xp.isnan(v)) == len(np.flatnonzero(mask_expected))

    encoder = create_encoder("grib")
    r = encoder.encode(values=v, template=f[0], check_nans=True, missing_value=9999)

    # re-read: the missing points must still be NaN
    f_r = r.to_field()
    v_r = array_convert(f_r.values, array_namespace="numpy").flatten()
    assert np.array_equal(np.isnan(v_r), mask_expected)
    assert np.allclose(v_r[~mask_expected], expected[~mask_expected], atol=0.01)


def _check_values_with_nan(message, expected):
    mask_expected = np.isnan(expected)
    f = from_source("memory", message).to_fieldlist()
    for dtype in (None, "float32"):
        v = f[0].to_numpy(flatten=True, dtype=dtype)
        assert np.array_equal(np.isnan(v), mask_expected)
        assert np.allclose(v[~mask_expected], expected[~mask_expected], atol=0.01)


@pytest.mark.parametrize(
    "sample,packing",
    [("GRIB1", "grid_simple"), ("GRIB2", "grid_simple"), ("GRIB2", "grid_ccsds")],
)
@pytest.mark.parametrize(
    "case",
    ["no_missing", "missing", "constant_with_missing", "all_missing"],
)
def test_grib_values_missing_bitmap_packing(sample, packing, case):
    """Simple and CCSDS packing use numberOfMissing to detect missing values."""
    h = eccodes.codes_grib_new_from_samples(sample)
    try:
        eccodes.codes_set(h, "packingType", packing)
        n = eccodes.codes_get(h, "numberOfValues")

        if case == "constant_with_missing":
            expected = np.full(n, 250.0)
        else:
            expected = np.linspace(200, 300, n)

        if case == "all_missing":
            missing_idx = list(range(n))
        elif case == "no_missing":
            missing_idx = []
        else:
            missing_idx = [0, 5, n // 4, n // 2, n - 1]

        values = expected.copy()
        values[missing_idx] = 9999
        expected[missing_idx] = np.nan

        eccodes.codes_set(h, "missingValue", 9999)
        eccodes.codes_set(h, "bitmapPresent", 0 if case == "no_missing" else 1)
        eccodes.codes_set(h, "bitsPerValue", 16)
        eccodes.codes_set_values(h, values)

        assert eccodes.codes_get(h, "packingType") == packing
        assert eccodes.codes_get(h, "numberOfMissing") == len(missing_idx)
        if case == "constant_with_missing":
            assert eccodes.codes_get(h, "bitsPerValue") == 0
        message = eccodes.codes_get_message(h)
    finally:
        eccodes.codes_release(h)

    _check_values_with_nan(message, expected)


def test_grib_values_missing_grib1_dummy_field():
    """A GRIB1 dummy field (binaryScaleFactor=-32767) has all values missing
    without a bitmap, and ecCodes gives no numberOfMissing for it.
    """
    h = eccodes.codes_grib_new_from_samples("GRIB1")
    try:
        n = eccodes.codes_get(h, "numberOfValues")
        eccodes.codes_set_values(h, np.linspace(200, 300, n))
        offset = eccodes.codes_get(h, "offsetSection4")
        message = bytearray(eccodes.codes_get_message(h))
    finally:
        eccodes.codes_release(h)

    # binaryScaleFactor is read-only, so set it in the binary data section
    # (octets 5-6 of section 4) to -32767
    message[offset + 4] = 0xFF
    message[offset + 5] = 0xFF
    message = bytes(message)

    h = eccodes.codes_new_from_message(message)
    try:
        assert eccodes.codes_get(h, "binaryScaleFactor") == -32767
        assert eccodes.codes_get(h, "packingType") == "grid_simple"
        assert eccodes.codes_get(h, "bitmapPresent") == 0
        assert not eccodes.codes_is_defined(h, "numberOfMissing")
    finally:
        eccodes.codes_release(h)

    _check_values_with_nan(message, np.full(n, np.nan))


def test_grib_immutable_values():
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    # the field access the values via the grib handle
    f = fl[0]

    v1 = f.to_numpy(copy=False)
    v2 = f.to_numpy(copy=False)
    assert v1 is not v2
    assert not np.shares_memory(v1, v2)

    v1 = f.to_numpy(copy=False)
    v2 = f.to_numpy(copy=True)
    assert v1 is not v2
    assert np.allclose(v1, v2)

    v_ori = f.values.copy()
    with pytest.raises(AttributeError):
        f.values = v_ori + 1

    with pytest.raises(AttributeError):
        f.values += 1

    f.values[:] += 1
    assert np.allclose(f.values, v_ori)

    assert f.values is not f.values
    assert not np.shares_memory(f.values, f.values)


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main()
