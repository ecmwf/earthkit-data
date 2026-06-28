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


def test_hl_csv_single_core():
    ds = from_source("file", earthkit_test_data_file("test.csv"))

    assert ds._TYPE_NAME == "CSV"
    assert ds.is_stream() is False
    assert "pandas" in ds.available_types

    df = ds.to_pandas()
    assert len(df) == 6
    assert list(df.columns) == ["h1", "h2", "h3", "name"]
