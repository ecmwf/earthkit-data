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

from earthkit.data import Field
from earthkit.data import from_source
from earthkit.data.utils.testing import NO_IRIS
from earthkit.data.utils.testing import earthkit_examples_file
from earthkit.data.utils.testing import earthkit_test_data_file


@pytest.mark.skip("Disabled at the moment")
@pytest.mark.skipif(NO_IRIS, reason="Iris or ncdata not installed")
def test_iris_source():
    ds = from_source("iris", earthkit_examples_file("air_temp.pp"))
    assert len(ds) == 1
    assert isinstance(ds[0], Field)
    assert ds[0].metadata("standard_name") == "air_temperature"


@pytest.mark.skip("Disabled at the moment")
@pytest.mark.skipif(NO_IRIS, reason="Iris or ncdata not installed")
def test_iris_source_wind():
    ds = from_source("iris", earthkit_test_data_file("wind_speed.pp"))
    assert len(ds) == 2
    assert isinstance(ds[0], Field)
    assert isinstance(ds[1], Field)
    assert ds[0].metadata("standard_name") == "x_wind"
    assert ds[1].metadata("standard_name") == "y_wind"
