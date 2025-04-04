#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.utils.testing import get_array_backend

from earthkit.data import from_source
from earthkit.data.testing import ARRAY_BACKENDS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file


def load_array_fieldlist(path, array_backend, **kwargs):
    ds = from_source("file", path, **kwargs)
    return ds.to_fieldlist(array_backend=array_backend)
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
        return from_source("file", path, **kwargs), get_array_backend("numpy")
    elif fl_type == "array":
        return load_array_fieldlist(path, "numpy", **kwargs), get_array_backend("numpy")
    elif fl_type == "memory":
        assert len(path) == 1
        with open(path[0], "rb") as f:
            ds = from_source("stream", f, read_all=True, **kwargs)
            len(ds)  # force reading
            return ds, get_array_backend("numpy")
    elif array_backend := get_array_backend(fl_type):
        return load_array_fieldlist(path, array_backend, **kwargs), array_backend
    else:
        raise ValueError(f"Invalid fl_type={fl_type}")


FL_TYPES = ["file"]
FL_TYPES.extend([b.name for b in ARRAY_BACKENDS])
FL_ARRAYS = [b.name for b in ARRAY_BACKENDS]
FL_NUMPY = ["file", "numpy"]
FL_FILE = ["file"]
