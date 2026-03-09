#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_object
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file


def test_hl_pandas_single_core():
    df = from_source("file", earthkit_test_data_file("test.csv")).to_pandas()

    series = df["h1"]
    ds = from_object(series)
    assert ds._TYPE_NAME == "pandas.Series"
    assert "pandas" in ds.available_types
    s2 = ds.to_pandas()
    assert s2.equals(series)

    ds = from_object(df)
    assert ds._TYPE_NAME == "pandas.DataFrame"
    assert "pandas" in ds.available_types
    df2 = ds.to_pandas()
    assert df2.equals(df)
