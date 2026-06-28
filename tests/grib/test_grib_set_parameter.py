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
from grib_fixtures import load_grib_data  # noqa: E402

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize(
    "_kwargs,ref1,ref_grib,ref2",
    [
        (
            {"parameter.variable": "q", "parameter.units": "kg/kg"},
            {
                "parameter.variable": "q",
                "metadata.param": None,
                "metadata.shortName": None,
                "parameter.units": "kg/kg",
                "metadata.units": None,
            },
            {
                "param": "t",
                "shortName": "t",
                "units": "K",
            },
            {
                "parameter.variable": "q",
                "metadata.param": "q",
                "metadata.shortName": "q",
                "metadata.units": "kg kg**-1",
            },
        ),
        # (
        #     {"param": "q", "units": "kg/kg"},
        #     {"variable": "q", "param": "q", "grib.shortName": "t", "units": "kg/kg", "grib.units": "K"},
        #     {"variable": "q", "param": "q", "grib.shortName": "q", "units": "kg kg**-1"},
        # ),
    ],
)
def test_grib_set_parameter_1(fl_type, _kwargs, ref1, ref_grib, ref2):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)

    for k, v in ref1.items():
        assert f.get(k) == v

    # the field still stores the original GRIB metadata as private metadata,
    # which is hidden but used when writing back to GRIB
    grib_md = f._get_grib()
    for k, v in ref_grib.items():
        assert grib_md.get(k) == v

    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        for k, v in ref2.items():
            assert f_saved[0].get(k) == v


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
def test_grib_set_parameter_2(
    fl_type,
):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set({"parameter.variable": "ta", "parameter.units": "kg/kg"})
    assert f.get("parameter.variable") == "ta"
    assert f.get("metadata.shortName") is None
    assert f.get("parameter.units") == "kg/kg"
    assert f.get("metadata.units") is None


# --------------------------------------------------------------------------
# Round-trip tests for GribParameterContextCollector keys
# --------------------------------------------------------------------------


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_parameter_chem_roundtrip(fl_type):
    """Set parameter.chem, write GRIB, read back and verify chemShortName."""
    ds_ori, _ = load_grib_data("chem-cams.grib", fl_type, folder="data")
    f = ds_ori[0]

    # Change chem from CO to SO2
    f2 = f.set({"parameter.chem": "SO2"})
    assert f2.get("parameter.chem") == "SO2"
    assert f2.get("parameter.variable") == "mass_mixrat"

    with temp_file() as tmp:
        f2.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        assert f_saved[0].get("parameter.variable") == "mass_mixrat"
        assert f_saved[0].get("parameter.chem") == "SO2"
        assert f_saved[0].get("metadata.shortName") == "mass_mixrat"
        assert f_saved[0].get("metadata.chemShortName") == "SO2"


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_parameter_chem_variable_roundtrip(fl_type):
    """Set both parameter.variable and parameter.chem, write GRIB, read back."""
    ds_ori, _ = load_grib_data("chem-cams.grib", fl_type, folder="data")
    f = ds_ori[0]

    f2 = f.set({"parameter.variable": "mass_mixrat", "parameter.chem": "HCHO"})
    assert f2.get("parameter.chem") == "HCHO"

    with temp_file() as tmp:
        f2.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        assert f_saved[0].get("parameter.variable") == "mass_mixrat"
        assert f_saved[0].get("parameter.chem") == "HCHO"
        assert f_saved[0].get("metadata.chemShortName") == "HCHO"


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_parameter_wavelength_roundtrip(fl_type):
    """Set parameter.wavelength (single value), write GRIB, read back."""
    ds_ori, _ = load_grib_data("optical-cams.grib", fl_type, folder="data")
    f = ds_ori[0]

    # Change wavelength from 550 to 800 nm
    f2 = f.set({"parameter.wavelength": 800, "parameter.wavelength_units": "nm"})
    assert f2.get("parameter.wavelength") == 800

    with temp_file() as tmp:
        f2.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        assert f_saved[0].get("parameter.wavelength") == 800
        assert f_saved[0].get("parameter.variable") == "aod"
        assert f_saved[0].get("metadata.shortName") == "aod"


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_parameter_wavelength_bounds_roundtrip(fl_type):
    """Set parameter.wavelength_bounds, write GRIB, verify raw GRIB keys."""
    ds_ori, _ = load_grib_data("optical-cams.grib", fl_type, folder="data")
    f = ds_ori[0]

    # Set wavelength with bounds
    f2 = f.set({
        "parameter.wavelength": 625,
        "parameter.wavelength_bounds": (500, 750),
        "parameter.wavelength_units": "nm",
    })
    assert f2.get("parameter.wavelength") == 625
    assert f2.get("parameter.wavelength_bounds") == (500, 750)

    with temp_file() as tmp:
        f2.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        assert f_saved[0].get("parameter.wavelength") == 625
        assert f_saved[0].get("parameter.wavelength_bounds") == (500, 750)


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_parameter_wave_direction_roundtrip(fl_type):
    """Set parameter.wave_direction_index, write GRIB, read back as 1-based directionNumber."""
    ds_ori, _ = load_grib_data("wave_spectra.grib", fl_type, folder="data")
    f = ds_ori[0]

    # Set a new direction index (0-based)
    f2 = f.set({
        "parameter.wave_direction_index": 3,
    })
    assert f2.get("parameter.wave_direction_index") == 3

    with temp_file() as tmp:
        f2.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        # 0-based index 3 should be stored as 1-based directionNumber=4
        assert f_saved[0].get("parameter.wave_direction_index") == 3
        assert f_saved[0].get("metadata.directionNumber") == 4


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_parameter_wave_frequency_roundtrip(fl_type):
    """Set parameter.wave_frequency_index, write GRIB, read back as 1-based frequencyNumber."""
    ds_ori, _ = load_grib_data("wave_spectra.grib", fl_type, folder="data")
    f = ds_ori[0]

    # Set a new frequency index (0-based)
    f2 = f.set({
        "parameter.wave_frequency_index": 2,
    })
    assert f2.get("parameter.wave_frequency_index") == 2

    with temp_file() as tmp:
        f2.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        # 0-based index 2 should be stored as 1-based frequencyNumber=3
        assert f_saved[0].get("parameter.wave_frequency_index") == 2
        assert f_saved[0].get("metadata.frequencyNumber") == 3


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_parameter_wave_both_indices_roundtrip(fl_type):
    """Set both wave_direction_index and wave_frequency_index, write, read back."""
    ds_ori, _ = load_grib_data("wave_spectra.grib", fl_type, folder="data")
    f = ds_ori[0]

    f2 = f.set({
        "parameter.wave_direction_index": 4,
        "parameter.wave_frequency_index": 7,
    })
    assert f2.get("parameter.wave_direction_index") == 4
    assert f2.get("parameter.wave_frequency_index") == 7

    with temp_file() as tmp:
        f2.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        # direction: 0-based 4 → 1-based 5
        assert f_saved[0].get("parameter.wave_direction_index") == 4
        assert f_saved[0].get("metadata.directionNumber") == 5
        # frequency: 0-based 7 → 1-based 8
        assert f_saved[0].get("parameter.wave_frequency_index") == 7
        assert f_saved[0].get("metadata.frequencyNumber") == 8
