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


def test_hl_shapefile_single_core():
    d = from_source("file", earthkit_test_data_file("NUTS_RG_20M_2021_3035.shp.zip"))

    assert d._TYPE_NAME == "Shapefile"
    assert "geopandas" in d.available_types

    df = d.to_pandas()
    assert len(df) == 2010
    r = df.iloc[1]
    assert r.NUTS_ID == "HR"
    assert r.NAME_LATN == "Hrvatska"
    assert len(r.geometry.geoms) == 16

    df = d.to_geopandas()
    assert len(df) == 2010
    r = df.iloc[1]
    assert r.NUTS_ID == "HR"
    assert r.NAME_LATN == "Hrvatska"
    assert len(r.geometry.geoms) == 16

    ds = d.to_xarray()
    assert "NUTS_ID" in ds.data_vars
    assert "NAME_LATN" in ds.data_vars
    assert "geometry" in ds.data_vars

    fl = d.to_featurelist()
    assert len(fl) == 2010

    v = d.to_numpy()
    assert v.shape == (2010, 10)

    v = d.to_numpy(flatten=True)
    assert v.shape == (2010 * 10,)
