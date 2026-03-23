#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging

import geopandas as gpd
import pandas as pd

from earthkit.data import from_object, transform

LOG = logging.getLogger(__name__)


def test_pd_series_translator():
    val = pd.Series([1, 2, 3])
    ds = from_object(val)

    assert transform(val, pd.Series).equals(val)
    assert transform(ds, pd.Series).equals(val)

    assert isinstance(transform(val, pd.Series), pd.Series)
    assert isinstance(transform(ds, pd.Series), pd.Series)


def test_pd_dataframe_translator():
    val = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    ds = from_object(val)

    assert transform(val, pd.DataFrame).equals(val)
    assert transform(ds, pd.DataFrame).equals(val)

    assert isinstance(transform(val, pd.DataFrame), pd.DataFrame)
    assert isinstance(transform(ds, pd.DataFrame), pd.DataFrame)


def test_gpd_dataframe_translator():
    val = gpd.GeoDataFrame()
    ds = from_object(val)

    assert transform(val, gpd.GeoDataFrame).equals(val)
    assert transform(ds, gpd.GeoDataFrame).equals(val)

    assert isinstance(transform(val, gpd.GeoDataFrame), gpd.GeoDataFrame)
    assert isinstance(transform(ds, gpd.GeoDataFrame), gpd.GeoDataFrame)
