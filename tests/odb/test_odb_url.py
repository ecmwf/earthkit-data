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
from earthkit.data.utils.testing import earthkit_remote_examples_file


def test_odb_url():
    ds = from_source("url", earthkit_remote_examples_file("test.odb"))
    assert "pandas" in ds.available_types
    df = ds.to_pandas()
    assert len(df) == 717
