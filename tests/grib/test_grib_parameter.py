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
    assert f.parameter.chem() == "CO"
    assert f.parameter.units() == "kg m**-2"


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_parameter_chem_long_name(fl_type):
    """Test chem_long_name extraction from CAMS chemistry GRIB2 data."""
    ds, _ = load_grib_data("chem-cams.grib", fl_type, folder="data")

    expected = [
        ("mass_mixrat", "CO", "Carbon monoxide"),
        ("mass_mixrat", "HCHO", "Formaldehyde"),
        ("mass_mixrat", "O3", "Ozone"),
    ]

    assert len(ds) == 3
    for i, (var, chem, chem_long) in enumerate(expected):
        f = ds[i]
        assert f.parameter.variable() == var
        assert f.parameter.param() == var
        assert f.parameter.units() == "dimensionless"
        assert f.parameter.chem() == chem
        assert f.parameter.chem_long_name() == chem_long
        assert f.parameter.wavelength() is None
        assert f.parameter.wave_direction() is None
        assert f.parameter.wave_frequency() is None


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_parameter_wavelength(fl_type):
    """Test wavelength extraction from CAMS optical GRIB2 data."""
    ds, _ = load_grib_data("optical-cams.grib", fl_type, folder="data")

    assert len(ds) == 4
    # All fields have aod variable with wavelength 550 or 800
    for f in ds:
        assert f.parameter.wavelength() in (550, 800)
        assert isinstance(f.parameter.wavelength(), int)

    result = ds.unique("parameter.wavelength")
    assert set(result["parameter.wavelength"]) == {550, 800}


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_parameter_wave_direction(fl_type):
    """Test wave_direction extraction from 2D wave spectra GRIB data."""
    ds, _ = load_grib_data("wave_spectra.grib", fl_type, folder="data")

    assert len(ds) == 18
    # All fields should have non-None wave_direction
    for f in ds:
        assert f.parameter.wave_direction() is not None
        assert isinstance(f.parameter.wave_direction(), float)

    result = ds.unique("parameter.wave_direction")
    assert set(result["parameter.wave_direction"]) == {55.0, 115.0, 175.0, 235.0, 295.0, 355.0}


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_parameter_wave_frequency(fl_type):
    """Test wave_frequency extraction from 2D wave spectra GRIB data."""
    ds, _ = load_grib_data("wave_spectra.grib", fl_type, folder="data")

    result = ds.unique("parameter.wave_frequency")
    freqs = result["parameter.wave_frequency"]
    assert len(freqs) == 3
    # Check approximate values
    assert abs(freqs[0] - 0.034523) < 0.001
    assert abs(freqs[1] - 0.1311) < 0.001
    assert abs(freqs[2] - 0.497852) < 0.001
