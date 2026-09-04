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
from earthkit.data.utils.testing import earthkit_test_data_file


def test_hl_multi_core():
    ds = from_source("file", [earthkit_test_data_file("binary_1"), earthkit_test_data_file("binary_2")], merger=False)

    assert ds._TYPE_NAME == "Multi"
    assert ds.is_stream() is False
    assert ds.available_types == []
    assert len(ds.path) == 2
    assert all(isinstance(p, str) for p in ds.path)
    assert ds.path[0].endswith("binary_1")
    assert ds.path[1].endswith("binary_2")
