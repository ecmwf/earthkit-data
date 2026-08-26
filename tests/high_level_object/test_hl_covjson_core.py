#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data import from_source
from earthkit.data.utils.testing import NO_COVJSONKIT, earthkit_test_data_file


@pytest.mark.skipif(NO_COVJSONKIT, reason="no covjsonkit available")
def test_hl_covjson_single_core():
    ds = from_source("file", earthkit_test_data_file("time_series.covjson"))
    assert ds

    assert ds._TYPE_NAME == "Covjson"
    assert ds.is_stream() is False
    assert "xarray" in ds.available_types
    assert "fieldlist" in ds.available_types
    assert "geojson" in ds.available_types
    assert isinstance(ds.path, str)

    a = ds.to_xarray()
    assert "2t" in a.data_vars
    assert a["2t"].shape == (1, 1, 1, 1, 1, 9)
    assert a.sizes == {"latitude": 1, "longitude": 1, "levelist": 1, "number": 1, "datetime": 1, "t": 9}

    fl = ds.to_fieldlist()
    assert fl
    assert len(fl) == 9
    assert fl.get("parameter.variable") == ["2t"] * 9
    assert fl[0].vertical.level() == 0
    assert fl[0].vertical.level_type() == "surface"

    gs = ds.to_geojson()
    assert gs
    assert len(gs["features"]) == 9
