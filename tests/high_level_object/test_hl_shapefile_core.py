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
from earthkit.data.utils.testing import earthkit_test_data_file


def test_hl_geopandas_single_core():
    import geopandas as gpd

    df = gpd.read_file(earthkit_test_data_file("NUTS_RG_20M_2021_3035.geojson"))

    ds = from_object(df)
    assert ds._TYPE_NAME == "geopandas.GeoDataFrame"
    assert "pandas" in ds.available_types
    df2 = ds.to_pandas()
    assert df2.equals(df)
    assert len(df2) == 2010

    fl = ds.to_featurelist()
    assert len(fl) == 2010
