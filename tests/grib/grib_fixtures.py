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
from earthkit.data.testing import ARRAY_BACKENDS
from earthkit.data.testing import ArrayBackend
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file


def load_array_fieldlist(path, array_namespace=None, device=None, dtype=None, **kwargs):
    ds = from_source("file", path, **kwargs)
    return ds.to_fieldlist(array_namespace=array_namespace, device=device, dtype=dtype)
    # return FieldList.from_array(
    #     ds.values, [m.override(generatingProcessIdentifier=120) for m in ds.metadata()]
    # )


def load_grib_data(filename, fl_type, folder="example", **kwargs):
    if isinstance(filename, str):
        filename = [filename]

    if folder == "example":
        path = [earthkit_examples_file(name) for name in filename]
    elif folder == "data":
        path = [earthkit_test_data_file(name) for name in filename]
    else:
        raise ValueError(f"Invalid folder={folder}")

    if fl_type == "file":
        backend = ArrayBackend("numpy")
        return from_source("file", path, **kwargs), backend
    elif fl_type == "array":
        backend = ArrayBackend("numpy")
        return load_array_fieldlist(path, array_namespace=backend.array_namespace, **kwargs), backend
    elif fl_type == "memory":
        assert len(path) == 1
        with open(path[0], "rb") as f:
            ds = from_source("stream", f, read_all=True, **kwargs)
            len(ds)  # force reading
            return ds, ArrayBackend("numpy")
    elif isinstance(fl_type, str):
        backend = ArrayBackend(fl_type)
        return load_array_fieldlist(path, array_namespace=backend.array_namespace, **kwargs), backend
    elif isinstance(fl_type, ArrayBackend):
        backend = fl_type
        return (
            load_array_fieldlist(
                path,
                array_namespace=backend.array_namespace,
                device=backend.device,
                dtype=backend.dtype,
                **kwargs,
            ),
            fl_type,
        )
    elif isinstance(fl_type, tuple):
        array_namespace = fl_type[0]
        device = fl_type[1] if len(fl_type) > 1 else None
        dtype = fl_type[2] if len(fl_type) > 2 else None
        backend = ArrayBackend(array_namespace, device, dtype)
        return (
            load_array_fieldlist(path, array_namespace=array_namespace, device=device, dtype=dtype, **kwargs),
            backend,
        )
    else:
        raise ValueError(f"Invalid fl_type={fl_type}")


FL_TYPES = ["file"]
FL_TYPES.extend([x for x in ARRAY_BACKENDS])
FL_ARRAYS = [x for x in ARRAY_BACKENDS]
FL_NUMPY = ["file", "numpy"]
FL_FILE = ["file"]
