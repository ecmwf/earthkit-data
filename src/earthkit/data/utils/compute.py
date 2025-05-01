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

from earthkit.data.wrappers import get_wrapper

COMP_UNARY = {"__neg__": lambda x: -x, "__pos__": lambda x: +x}

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


class Compute(metaclass=ABCMeta):
    def __init__(self, x):
        self.x = x
        if len(x) == 0:
            raise ValueError("FieldList x must not be empty")

    @abstractmethod
    def unary_op(self, oper):
        pass

    @abstractmethod
    def binary_op(self, oper, y):
        pass


class LoopCompute(Compute):
    def create_fieldlist(self, y):
        from earthkit.data.core.fieldlist import Field
        from earthkit.data.core.fieldlist import FieldList

        y = get_wrapper(y)

        if isinstance(y, FieldList):
            return y

        from earthkit.data.sources.array_list import from_array
        from earthkit.data.utils.metadata.dict import UserMetadata

        if isinstance(y, Field):
            return FieldList.from_fields([y])
        elif hasattr(y, "values"):
            x_field_shape = self.x[0].shape
            y_val = y.values
            from earthkit.utils.array import array_namespace

            xp = array_namespace(y_val)
            y_val = xp.asarray(y_val)

            # single value
            if y_val.size == 1:
                return from_array([y_val], [UserMetadata()])
            # multiple values
            else:
                y_shape = y_val.shape
                if len(y_shape) > 1:
                    y_field_shape = y_shape[1:]
                    if math.prod(x_field_shape) == math.prod(y_field_shape):
                        return from_array(y_val, [UserMetadata()] * y_shape[0])
                elif math.prod(x_field_shape) == math.prod(y_shape):
                    return from_array([y_val], [UserMetadata()])
                elif y_shape[0] == len(self.x):
                    return from_array(y_val, [UserMetadata()] * y_shape[0])

            assumed_x_shape = tuple(len(self.x), **x_field_shape)

            raise ValueError(f"y shape={y.shape} cannot be used with x shape={assumed_x_shape}")

        raise ValueError(f"y type={type(y)} cannot be used with x type={type(self.x)}")

    def unary_op(self, oper):
        r = []
        for f in self.x:
            f = f._unary_op(oper)
            # f.to_disk()
            r.append(f)
        return self.x.from_fields(r)

    def binary_op(self, oper, y):
        from earthkit.data.core.fieldlist import FieldList

        assert isinstance(self.x, FieldList)

        x = self.x
        y = self.create_fieldlist(y)
        assert isinstance(y, FieldList)

        if len(y) == 0:
            raise ValueError("FieldList y must not be empty")
        if len(self.x) != len(y):
            from itertools import repeat

            if len(self.x) == 1:
                x = repeat(self.x[0])
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


methods = {"loop": LoopCompute}


def get_method(method, *args, **kwargs):
    m = methods.get(method)
    if m is None:
        raise ValueError(f"Unknown method: {method}")
    return m(*args, **kwargs)
