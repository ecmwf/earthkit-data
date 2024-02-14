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
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.testing import earthkit_examples_file, earthkit_test_data_file


def load_array_fieldlist(path, backend):
    ds = from_source("file", path, backend=backend)
    return FieldList.from_array(
        ds.values, [m.override(generatingProcessIdentifier=120) for m in ds.metadata()]
    )


def load_grib_data(filename, fl_type, backend, folder="example"):
    if folder == "example":
        path = earthkit_examples_file(filename)
    elif folder == "data":
        path = earthkit_test_data_file(filename)
    else:
        raise ValueError("Invalid folder={folder}")

    if fl_type == "file":
        return from_source("file", path, backend=backend)
    elif fl_type == "array":
        return load_array_fieldlist(path, backend)
    else:
        raise ValueError("Invalid fl_type={fl_type}")


# def check_numpy_array_type(v, dtype=None):
#     import numpy as np

#     assert isinstance(v, np.ndarray)
#     if dtype is not None:
#         if dtype == "float64":
#             dtype = np.float64
#         elif dtype == "float32":
#             dtype = np.float32
#         else:
#             raise ValueError("Unsupported dtype={dtype}")
#         assert v.dtype == dtype


# def check_pytorch_array_type(v, dtype=None):
#     import torch

#     assert torch.is_tensor(v)
#     if dtype is not None:
#         if dtype == "float64":
#             dtype = torch.float64
#         elif dtype == "float32":
#             dtype = torch.float32
#         else:
#             raise ValueError("Unsupported dtype={dtype}")
#         assert v.dtype == dtype


# def check_array_type(v, backend, **kwargs):
#     if backend is None or backend == "numpy":
#         check_numpy_array_type(v, **kwargs)
#     elif backend == "pytorch":
#         check_pytorch_array_type(v, **kwargs)
#     else:
#         raise ValueError("Invalid backend={backend}")


# def get_array_namespace(backend):
#     from earthkit.data.core.array import ensure_backend

#     return ensure_backend(backend).array_ns


# def get_array(v, backend):
#     from earthkit.data.core.array import ensure_backend

#     b = ensure_backend(backend)
#     return b.from_other(v)


FL_TYPES = ["file", "array"]

# ARRAY_BACKENDS = ["numpy"]
# if not NO_PYTORCH:
#     ARRAY_BACKENDS.append("pytorch")
