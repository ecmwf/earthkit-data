# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


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
}


def _unary_op(self, oper, x):
    v = oper(self.values)
    r = self.clone(values=v)
    return r


def _binary_op(oper, x, y):
    from earthkit.data.wrappers import get_wrapper

    x = get_wrapper(x)
    y = get_wrapper(y)
    vx = x.values
    vy = y.values
    v = oper(vx, vy)
    r = x.clone(values=v)
    return r


# def apply_ufunc(func, *args, **kwargs):
#     """Apply a ufunc to the data.

#     Parameters
#     ----------
#     func : callable
#         The function to apply to the data.
#     args : tuple
#         The arguments to pass to the function.
#     kwargs : dict
#         The keyword arguments to pass to the function.

#     Returns
#     -------
#     FieldList
#         A new FieldList containing the results of applying the function to the data.
#     """


class Compute:
    pass


class LoopCompute(Compute):
    @staticmethod
    def unary_op(oper, x):
        from .fieldlist import FieldList

        r = []
        for f in x:
            f = f._unary_op(oper)
            f.to_disk()
            r.append(f)
        return FieldList.from_fields(r)

    @staticmethod
    def binary_op(oper, x, y):
        from .fieldlist import Field
        from .fieldlist import FieldList

        r = []

        from itertools import repeat

        if isinstance(x, FieldList) and isinstance(y, FieldList):
            if len(x) == 0:
                raise ValueError("FieldList x must not be empty")
            if len(y) == 0:
                raise ValueError("FieldList y must not be empty")
            if len(x) != len(y):
                if len(x) == 1:
                    x = repeat(x[0])
                elif len(y) == 1:
                    y = repeat(y[0])
                else:
                    raise ValueError("FieldLists must have the same length")
        elif isinstance(x, FieldList):
            if isinstance(y, Field):
                y = repeat(y)
            elif isinstance(y, (float, int)):
                y = repeat(y)
            else:
                raise ValueError("FieldList and Field must be of the same type")
        elif isinstance(y, FieldList):
            if isinstance(x, Field):
                y = repeat(get_wrapper(y))
            elif isinstance(y, (float, int)):
                y = repeat(get_wrapper(y))
            else:
                raise ValueError("Unsupported type for y")

        else:
            raise ValueError("Either x or y must be a FieldList")

        for f1, f2 in zip(x, y):
            f = f1._binary_op(oper, f2)
            # f.to_disk()
            r.append(f)
        return FieldList.from_fields(r)

    # @staticmethod
    # def apply_ufunc(func, *args, **kwargs):
    #     x = [get_wrapper(a) for a in args]
    #     num = 0
    #     for i in range(num):
    #         v = func(*[a.values for a in x[i]], **kwargs)
    #         return v


class FullBlockCompute(Compute):
    @staticmethod
    def unary_op(oper, x):
        from earthkit.data import SimpleFieldList

        v = oper(x.values)
        r = []
        for vx, f in zip(x, v):
            f1 = f.clone(values=vx)
            f1.to_disk()
            r.append(f1)
        return SimpleFieldList(r)

    @staticmethod
    def binary_op(oper, x, y):
        from earthkit.data import SimpleFieldList

        from .fieldlist import Field
        from .fieldlist import FieldList

        r = []

        from itertools import repeat

        # num = None
        if isinstance(x, FieldList) and isinstance(y, FieldList):
            if len(x) != len(y):
                if len(x) == 1:
                    x = repeat(x[0])
                    # num = 1
                elif len(y) == 1:
                    y = repeat(y[0])
                else:
                    raise ValueError("FieldLists must have the same length")

        elif isinstance(x, FieldList):
            if isinstance(y, Field):
                y = repeat(y)
            elif isinstance(y, (float, int)):
                y = repeat(get_wrapper(y))
            else:
                raise ValueError("FieldList and Field must be of the same type")
        else:
            raise ValueError("FieldList and Field must be of the same type")

        v1 = x.values
        v2 = get_wrapper(y).values
        v = oper(v1, v2)

        for f, vx in zip(x, v):
            f1 = f.clone(values=vx)
            f1.to_disk()
            r.append(f)
        return SimpleFieldList(r)


methods = {"loop": LoopCompute, "all": FullBlockCompute}


def get_method(method):
    m = methods.get(method)
    if m is None:
        raise ValueError(f"Unknown method: {method}")


# class FieldList:
#     method = "loop"

#     # def __add__(self, other):
#     #     return self._binary_op(comp["__add__"], self, other)

#     # def __radd__(self, other):
#     #     return self._binary_op(comp["__radd__"], self, other)

#     def __getattr__(self, name):
#         from functools import partial

#         if name in COMP_UNARY:
#             op = COMP_UNARY[name]
#             return partial(self._unary_op, self, op)
#         elif name in COMP_BINARY:
#             op = COMP_BINARY[name]
#             return partial(self._binary_op, self, op)
#         else:
#             return super().__getattr__(name)

#     @staticmethod
#     def _unary_op(oper, x, method=None):
#         # x = get_wrapper(x)

#         if method == "loop":
#             return LoopCompute.unary_op(oper, x)
#         elif method == "all":
#             return FullBlockCompute.unary_op(oper, x)

#         raise ValueError(f"Unknown method: {method}")

#     @staticmethod
#     def _binary_op(oper, x, y, method=None):
#         # x = get_wrapper(x)
#         # y = get_wrapper(y)

#         if method == "loop":
#             return LoopCompute.binary_op(oper, x, y)
#         elif method == "all":
#             return FullBlockCompute.binary_op(oper, x, y)

#         raise ValueError(f"Unknown method: {method}")
