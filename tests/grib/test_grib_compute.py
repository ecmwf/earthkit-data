#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import math
import os
import sys

import numpy as np
import pytest

from earthkit.data.utils.compute import apply_ufunc

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_NUMPY  # noqa: E402
from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


class ComputeOperand:
    def __init__(self, ds, array_namespace=None, device=None):
        self.ds = ds
        self.array_namespace = array_namespace
        self.device = device


class SingleValueIntOperand(ComputeOperand):
    def val(self):
        return 10, 10


class SingleValueFloatOperand(ComputeOperand):
    def val(self):
        return 10.1, 10.1


class ArraySingleValueOperand(ComputeOperand):
    def val(self):
        xp = self.array_namespace
        v = xp.asarray([(i + 1) * 10 for i in range(len(self.ds))])

        size = self.ds[0].values.size
        if callable(size):
            size = math.prod(self.ds[0].values.shape)

        z = xp.zeros(size)
        z = [z + xp.asarray((i + 1) * 10) for i in range(len(self.ds))]
        v_ref = xp.stack(z)
        return v, v_ref


class ArrayFieldOperand(ComputeOperand):
    def val(self):
        xp = self.array_namespace
        return self.ds[0].values, xp.asarray([self.ds[0].values for _ in range(len(self.ds))])


class ArrayFieldListOperand(ComputeOperand):
    def val(self):
        return self.ds.values, self.ds.values


class FieldOperand(ComputeOperand):
    def val(self):
        return self.ds[0], self.ds[0].values


class SingleFieldListOperand(ComputeOperand):
    def val(self):
        f = self.ds.from_fields([self.ds[0]])
        return f, f.values


class FieldListOperand(ComputeOperand):
    def val(self):
        return self.ds, self.ds.values


class FieldUnaryOperand(ComputeOperand):
    def val(self):
        return self.ds[0], self.ds[0].values


class FieldListUnaryOperand(ComputeOperand):
    def val(self):
        return self.ds, self.ds.values


RIGHT_OPERANDS = [
    SingleValueIntOperand,
    SingleValueFloatOperand,
    ArraySingleValueOperand,
    ArrayFieldOperand,
    ArrayFieldListOperand,
    FieldOperand,
    SingleFieldListOperand,
    FieldListOperand,
]

# arrays cannot be left operands
LEFT_OPERANDS = [
    SingleValueIntOperand,
    SingleValueFloatOperand,
    FieldOperand,
    SingleFieldListOperand,
    FieldListOperand,
]

UNARY_OPERANDS = [
    FieldUnaryOperand,
    FieldListUnaryOperand,
]


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", RIGHT_OPERANDS)
def test_grib_compute_add(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend

    rval, rval_ref = operand(ds, xp, device).val()

    res = ds + rval
    ref = ds.values + rval_ref
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", RIGHT_OPERANDS)
def test_grib_compute_sub(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend

    rval, rval_ref = operand(ds, xp, device).val()

    res = ds - rval
    ref = ds.values - rval_ref
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", RIGHT_OPERANDS)
def test_grib_compute_mul(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    rval, rval_ref = operand(ds, xp, device).val()

    res = ds * rval
    ref = ds.values * rval_ref
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", RIGHT_OPERANDS)
def test_grib_compute_div(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    rval, rval_ref = operand(ds, xp, device).val()

    res = ds / rval
    ref = ds.values / rval_ref
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", RIGHT_OPERANDS)
def test_grib_compute_floordiv(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    rval, rval_ref = operand(ds, xp, device).val()

    res = ds // rval
    ref = ds.values // rval_ref
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", RIGHT_OPERANDS)
def test_grib_compute_mod(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    rval, rval_ref = operand(ds, xp, device).val()

    res = ds % rval
    ref = ds.values % rval_ref
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", RIGHT_OPERANDS)
def test_grib_compute_pow(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    rval, rval_ref = operand(ds, xp, device).val()

    res = ds**rval
    ref = ds.values**rval_ref
    assert xp.allclose(res.values, ref, equal_nan=True)


FieldOperand,


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", LEFT_OPERANDS)
def test_grib_compute_radd(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    lval, lval_ref = operand(ds, xp, device).val()

    res = lval + ds
    ref = lval_ref + ds.values

    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", LEFT_OPERANDS)
def test_grib_compute_rsub(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    lval, lval_ref = operand(ds, xp, device).val()

    res = lval - ds
    ref = lval_ref - ds.values
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", LEFT_OPERANDS)
def test_grib_compute_rmul(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    lval, lval_ref = operand(ds, xp, device).val()

    res = lval * ds
    ref = lval_ref * ds.values
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", LEFT_OPERANDS)
def test_grib_compute_rdiv(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    lval, lval_ref = operand(ds, xp, device).val()

    res = lval / ds
    ref = lval_ref / ds.values
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", LEFT_OPERANDS)
def test_grib_compute_rfloordiv(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    lval, lval_ref = operand(ds, xp, device).val()

    res = lval // ds
    ref = lval_ref // ds.values
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", LEFT_OPERANDS)
def test_grib_compute_rmod(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    lval, lval_ref = operand(ds, xp, device).val()

    res = lval % ds
    ref = lval_ref % ds.values
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", LEFT_OPERANDS)
def test_grib_compute_rpow(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    lval, lval_ref = operand(ds, xp, device).val()

    res = lval**ds
    ref = lval_ref**ds.values
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", UNARY_OPERANDS)
def test_grib_compute_pos(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, _, _ = array_backend
    val, val_ref = operand(ds).val()

    res = +val
    ref = val_ref
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("operand", UNARY_OPERANDS)
def test_grib_compute_neg(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    val, val_ref = operand(ds, xp, device).val()

    res = -val
    ref = -val_ref
    assert xp.allclose(res.values, ref, equal_nan=True)


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("operand", UNARY_OPERANDS)
def test_grib_compute_ufunc(fl_type, operand):
    ds, array_backend = load_grib_data("test.grib", fl_type)
    xp, device, _ = array_backend
    val, val_ref = operand(ds, xp, device).val()

    def func(x, y):
        return np.sin(x) + y * 2

    ds1 = val
    ds2 = val + 1

    res = apply_ufunc(func, ds1, ds2)
    ref = func(val_ref, val_ref + 1)
    assert xp.allclose(res.values, ref, equal_nan=True)
