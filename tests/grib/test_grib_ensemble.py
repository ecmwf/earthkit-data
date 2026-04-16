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
from grib_fixtures import (
    load_grib_data,  # noqa: E402
)


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_ensemble_1(fl_type):
    ds, _ = load_grib_data("ens_50.grib", fl_type, folder="data")
    f = ds[0]

    assert f.ensemble.member() == "1"
    assert f.ensemble.realization() == "1"
    assert f.ensemble.realisation() == "1"


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_ensemble_2(fl_type):
    ds, _ = load_grib_data("test.grib", fl_type)
    f = ds[0]

    assert f.ensemble.member() == "0"
    assert f.ensemble.realization() == "0"
    assert f.ensemble.realisation() == "0"


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_ensemble_3(fl_type):
    ds, _ = load_grib_data("ens_none.grib", fl_type, folder="data")
    f = ds[0]

    assert f.ensemble.member() is None
    assert f.ensemble.realization() is None
    assert f.ensemble.realisation() is None
