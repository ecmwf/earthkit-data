#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.field import Field
from earthkit.data.core.temporary import temp_file


@pytest.mark.long_test
@pytest.mark.download
def test_netcdf_opendap():
    url = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2/sst.mnmean.nc"
    ds = from_source("opendap", url)

    assert len(ds) == 494
    assert ds[0:2].get("parameter.variable") == ["sst", "sst"]
    v = ds[0].values
    assert v.shape == (64800,)
    assert np.isclose(v.mean(), 11.8082780)
    v = ds[0].to_numpy()
    assert v.shape == (180, 360)
    assert np.isclose(v.mean(), 11.8082780)

    x = ds.to_xarray()
    assert len(x.data_vars) == 2
    assert list(x["sst"].dims) == ["time", "lat", "lon"]
    assert x["sst"].shape == (494, 180, 360)

    with temp_file() as path:
        ds.to_target("file", path)

        ds1 = from_source("file", path)
        assert len(ds1) == 494
        assert isinstance(ds1[0], Field)
        assert ds1[0:2].get("parameter.variable") == ["sst", "sst"]


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main()
