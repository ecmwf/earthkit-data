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
from earthkit.data.testing import earthkit_examples_file


def test_file_pattern_source_grib():
    ds = from_source("file-pattern", earthkit_examples_file("test{id}.grib"), {"id": [4, 6]})

    assert len(ds) == 10
    assert ds.metadata("param") == ["t", "z", "t", "z", "t", "u", "v", "t", "u", "v"]
