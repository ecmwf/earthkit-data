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
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.utils.array import get_backend


def load_array_fieldlist(path, array_backend):
    ds = from_source("file", path)
    return ds.to_fieldlist(array_backend=array_backend)
    # return FieldList.from_array(
    #     ds.values, [m.override(generatingProcessIdentifier=120) for m in ds.metadata()]
    # )


def load_grib_data(filename, fl_type, folder="example"):
    if isinstance(filename, str):
        filename = [filename]

    if folder == "example":
        path = [earthkit_examples_file(name) for name in filename]
    elif folder == "data":
        path = [earthkit_test_data_file(name) for name in filename]
    else:
        raise ValueError("Invalid folder={folder}")

    if fl_type == "file":
        return from_source("file", path), get_backend("numpy")
    elif fl_type in ARRAY_BACKENDS:
        array_backend = fl_type
        return load_array_fieldlist(path, array_backend), get_backend(array_backend)
    else:
        raise ValueError("Invalid fl_type={fl_type}")


FL_TYPES = ["file"]
FL_TYPES.extend(ARRAY_BACKENDS)
FL_ARRAYS = ARRAY_BACKENDS
FL_NUMPY = ["file", "numpy"]
FL_FILE = ["file"]
