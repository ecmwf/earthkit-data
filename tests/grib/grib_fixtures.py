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
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file


def load_array_fieldlist(path, array_backend):
    ds = from_source("file", path, array_backend=array_backend)
    return FieldList.from_array(
        ds.values, [m.override(generatingProcessIdentifier=120) for m in ds.metadata()]
    )


def load_grib_data(filename, fl_type, array_backend, folder="example"):
    if folder == "example":
        path = earthkit_examples_file(filename)
    elif folder == "data":
        path = earthkit_test_data_file(filename)
    else:
        raise ValueError("Invalid folder={folder}")

    if fl_type == "file":
        return from_source("file", path, array_backend=array_backend)
    elif fl_type == "array":
        return load_array_fieldlist(path, array_backend)
    else:
        raise ValueError("Invalid fl_type={fl_type}")


FL_TYPES = ["file", "array"]
