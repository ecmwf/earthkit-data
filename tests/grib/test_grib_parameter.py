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
    FL_FILE,  # noqa: E402
    FL_TYPES,  # noqa: E402
    load_grib_data,  # noqa: E402
)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_parameter_1(fl_type):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    f = ds[0]

    assert f.parameter.variable() == "2t"
    assert f.parameter.standard_name() == "unknown"
    assert f.parameter.long_name() == "2 metre temperature"
    assert f.parameter.param() == "2t"
    assert f.parameter.units() == "K"


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_parameter_2(fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)
    f = ds[0]

    assert f.parameter.variable() == "t"
    assert f.parameter.standard_name() == "air_temperature"
    assert f.parameter.long_name() == "Temperature"
    assert f.parameter.param() == "t"
    assert f.parameter.units() == "K"


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_parameter_tilde_shortname(fl_type):
    # the shortName is ~ in the grib file
    # but the paramId is 106
    ds, _ = load_grib_data("tilde_shortname.grib", fl_type, folder="data")
    f = ds[0]

    assert f.parameter.variable() == "106"
    assert f.parameter.param() == "106"
    assert f.parameter.units() == "~"
    assert f.parameter.standard_name() == "unknown"
    assert f.parameter.long_name() == "Experimental product"


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_parameter_chem(fl_type):
    ds, _ = load_grib_data("chem_ll.grib2", fl_type, folder="data")
    f = ds[0]

    assert f.parameter.variable() == "tcvimd"
    assert f.parameter.param() == "tcvimd"
    assert f.parameter.chem_variable() == "CO"
    assert f.parameter.units() == "kg m**-2"
