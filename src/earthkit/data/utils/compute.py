# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import math
from abc import ABCMeta
from abc import abstractmethod

from earthkit.utils.array import array_namespace

from earthkit.data.wrappers import get_wrapper

COMP_UNARY = {
    "__neg__": lambda x: -x,
    "__pos__": lambda x: +x,
    "asin": lambda x: array_namespace(x).asin(x),
    "acos": lambda x: array_namespace(x).acos(x),
    "atan": lambda x: array_namespace(x).atan(x),
    "arcsin": lambda x: array_namespace(x).asin(x),
    "arccos": lambda x: array_namespace(x).acos(x),
    "arctan": lambda x: array_namespace(x).atan(x),
    "cos": lambda x: array_namespace(x).cos(x),
    "cosh": lambda x: array_namespace(x).cosh(x),
    "exp": lambda x: array_namespace(x).exp(x),
    "floor": lambda x: array_namespace(x).floor(x),
    "log": lambda x: array_namespace(x).log(x),
    "log10": lambda x: array_namespace(x).log10(x),
    "round": lambda x: array_namespace(x).round(x),
    "sign": lambda x: array_namespace(x).sign(x),
    "sin": lambda x: array_namespace(x).sin(x),
    "sinh": lambda x: array_namespace(x).sinh(x),
    "tan": lambda x: array_namespace(x).tan(x),
    "tanh": lambda x: array_namespace(x).tanh(x),
    "sqrt": lambda x: array_namespace(x).sqrt(x),
    "trunc": lambda x: array_namespace(x).trunc(x),
}

COMP_BINARY = {
    "__add__": lambda x, y: x + y,
    "__radd__": lambda x, y: y + x,
    "__sub__": lambda x, y: x - y,
    "__rsub__": lambda x, y: y - x,
    "__mul__": lambda x, y: x * y,
    "__rmul__": lambda x, y: y * x,
    "__truediv__": lambda x, y: x / y,
    "__rtruediv__": lambda x, y: y / x,
    "__floordiv__": lambda x, y: x // y,
    "__rfloordiv__": lambda x, y: y // x,
    "__mod__": lambda x, y: x % y,
    "__rmod__": lambda x, y: y % x,
    "__pow__": lambda x, y: x**y,
    "__rpow__": lambda x, y: y**x,
    "__gt__": lambda x, y: x > y,
    "__lt__": lambda x, y: x < y,
    "__ge__": lambda x, y: x >= y,
    "__le__": lambda x, y: x <= y,
    # "__eq__": lambda x, y: x == y,
    "__ne__": lambda x, y: x != y,
}


def wrap_maths(cls):
    def wrap_unary_method(op):
        def wrapper(self, *args, **kwargs):
            return self._unary_op(op, *args, **kwargs)

        return wrapper

    def wrap_binary_method(op):
        def wrapper(self, *args, **kwargs):
            return self._binary_op(op, *args, **kwargs)

        return wrapper

    for name in COMP_BINARY:
        op = COMP_BINARY[name]
        setattr(cls, name, wrap_binary_method(op))
    for name in COMP_UNARY:
        op = COMP_UNARY[name]
        setattr(cls, name, wrap_unary_method(op))
    return cls


def apply_ufunc(func, *args):
    from earthkit.data.core.field import Field
    from earthkit.data.core.fieldlist import FieldListCore
    from earthkit.data.indexing.fieldlist import FieldList

    x = [get_wrapper(a) for a in args]

    d = None

    if len(x) == 1:
        d = x[0]
        return d._unary_op(func)
    else:
        num = 0
        for a in x:
            if isinstance(a, FieldListCore):
                n = len(a)
                if n > num:
                    num = n
                    d = a
        if d is not None:
            return get_method("loop").apply_ufunc(func, d, *x)

        for a in x:
            if isinstance(a, Field):
                d = a
                d = FieldList.from_fields([d])
                r = get_method("loop").apply_ufunc(func, d, *x)
                assert len(r) == 1
                return r

        if all(hasattr(a, "values") for a in x):
            return func([f.values for f in x])

    raise ValueError("Cannot find a suitable object to apply ufunc")


class Compute(metaclass=ABCMeta):
    @abstractmethod
    def unary_op(self, oper):
        pass

    @abstractmethod
    def binary_op(self, oper, y):
        pass


class LoopCompute(Compute):
    @staticmethod
    def create_fieldlist(ref, x):
        from earthkit.data.core.field import Field
        from earthkit.data.core.fieldlist import FieldListCore
        from earthkit.data.indexing.fieldlist import FieldList

        x = get_wrapper(x)

        if isinstance(x, FieldListCore):
            return x

        if isinstance(x, Field):
            return FieldList.from_fields([x])
        elif hasattr(x, "values"):
            # from earthkit.data.sources.array_list import from_array
            # from earthkit.data.utils.metadata.dict import UserMetadata

            x_val = x.values
            from earthkit.utils.array import array_namespace

            xp = array_namespace(x_val)
            x_val = xp.asarray(x_val)

            def _make_fieldlist(values, n=1):
                if n == 1:
                    return FieldList.from_fields([Field.from_dict({"values": values})])
                else:
                    _f = []
                    for v in values:
                        _f.append(Field.from_dict({"values": v}))
                    return FieldList.from_fields(_f)

            # single value
            if x_val.size == 1:
                # return from_array([x_val], [UserMetadata()])
                return _make_fieldlist(x_val)
            # multiple values
            else:
                ref_field_shape = ref[0].shape
                x_shape = x_val.shape
                if len(x_shape) > 1:
                    x_field_shape = x_shape[1:]
                    if math.prod(ref_field_shape) == math.prod(x_field_shape):
                        return _make_fieldlist(x_val, n=x_shape[0])
                        # return from_array(x_val, [UserMetadata()] * x_shape[0])
                elif math.prod(ref_field_shape) == math.prod(x_shape):
                    return _make_fieldlist(x_val)
                    # return from_array([x_val], [UserMetadata()])
                elif x_shape[0] == len(ref):
                    return _make_fieldlist(x_val, n=x_shape[0])
                    # return from_array(x_val, [UserMetadata()] * x_shape[0])

            assumed_ref_shape = tuple(len(ref), **ref_field_shape)
            raise ValueError(f"y shape={x.shape} cannot be used with x shape={assumed_ref_shape}")

        raise ValueError(f"y type={type(x)} cannot be used with x type={type(ref)}")

    @staticmethod
    def unary_op(oper, x):
        r = []
        for f in x:
            f = f._unary_op(oper)
            # f.to_disk()
            r.append(f)
        return x.from_fields(r)

    @staticmethod
    def binary_op(oper, x, y):
        from earthkit.data.core.fieldlist import FieldListCore
        from earthkit.data.indexing.fieldlist import FieldList

        assert isinstance(x, FieldListCore), f"Expected FieldListCore for x, got {type(x)}"

        y = LoopCompute.create_fieldlist(x, y)
        assert isinstance(y, FieldListCore), f"Expected FieldListCore for y, got {type(y)}"

        if len(y) == 0:
            raise ValueError("FieldList y must not be empty")
        if len(x) != len(y):
            from itertools import repeat

            if len(x) == 1:
                x = repeat(x[0])
            elif len(y) == 1:
                y = repeat(y[0])
            else:
                raise ValueError("FieldLists must have the same length or one of them must be 1")

        r = []
        for f1, f2 in zip(x, y):
            f = f1._binary_op(oper, f2)
            # f.to_disk()
            r.append(f)

        return FieldList.from_fields(r)

    @staticmethod
    def apply_ufunc(func, ref, *args, template=None):
        from earthkit.data.indexing.fieldlist import FieldList

        x = [get_wrapper(a) for a in args]
        ds = []
        for i, a in enumerate(x):
            if a is not ref:
                a = LoopCompute.create_fieldlist(ref, a)
                if len(a) == 0:
                    raise ValueError(f"FieldList {a} at index={i} must not be empty")
                if len(ref) != len(a):
                    from itertools import repeat

                    if len(a) == 1:
                        a = repeat(a[0])
                    else:
                        raise ValueError("FieldLists must have the same length or one of them must be 1")
            ds.append(a)

        r = []
        for f_ref, *f_ds in zip(ref, *ds):
            x = [f.values for f in f_ds]
            vx = func(*x)
            f = f_ref.set(values=vx)
            # f.to_disk()
            r.append(f)
        return FieldList.from_fields(r)


methods = {"loop": LoopCompute}


def get_method(method):
    m = methods.get(method)
    if m is None:
        raise ValueError(f"Unknown method: {method}")
    return m
