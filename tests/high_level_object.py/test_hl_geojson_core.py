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


def test_hl_geojson_single_core():
    ds = from_source("file", earthkit_test_data_file("NUTS_RG_20M_2021_3035.geojson"))

    assert ds._TYPE_NAME == "GeoJSON"
    assert "pandas" in ds.available_types
    df = ds.to_pandas()
    assert len(df) == 2010
    assert list(df.columns) == [
        "id",
        "NUTS_ID",
        "LEVL_CODE",
        "CNTR_CODE",
        "NAME_LATN",
        "NUTS_NAME",
        "MOUNT_TYPE",
        "URBN_TYPE",
        "COAST_TYPE",
        "FID",
        "geometry",
    ]

    fl = ds.to_featurelist()
    assert len(fl) == 2010
