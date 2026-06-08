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

from earthkit.data.field.component.parameter import (
    ChemicalOpticalParameter,
    ChemicalParameter,
    OpticalParameter,
    Parameter,
    WaveSpectraParameter,
    create_parameter,
)


def test_parameter_component_alias_1():
    r = Parameter(variable="t", units="K")
    assert r.variable() == "t"
    assert r.param() == "t"
    assert r.units() == "K"
    assert r.standard_name() is None
    assert r.long_name() is None
    assert r.chem() is None
    assert r.chem_long_name() is None
    assert r.wavelength() is None
    assert r.wave_direction() is None
    assert r.wave_frequency() is None


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            [{"variable": "t", "units": "K"}, {"param": "t", "units": "K"}],
            {"variable": "t", "param": "t", "units": "K", "standard_name": None, "long_name": None},
        ),
        (
            {"variable": "t", "units": "K", "standard_name": "air_temperature", "long_name": "Temperature"},
            {
                "variable": "t",
                "param": "t",
                "units": "K",
                "standard_name": "air_temperature",
                "long_name": "Temperature",
            },
        ),
        (
            {
                "variable": "aod",
                "standard_name": "unknown",
                "long_name": "Aerosol optical depth",
                "units": "Numeric",
                "chem": "aer_total",
                "chem_long_name": "Total aerosol",
                "wavelength": 550,
                "wave_direction": None,
                "wave_frequency": None,
            },
            {
                "variable": "aod",
                "param": "aod",
                "standard_name": "unknown",
                "long_name": "Aerosol optical depth",
                "units": "Numeric",
                "chem": "aer_total",
                "chem_long_name": "Total aerosol",
                "wavelength": 550,
                "wave_direction": None,
                "wave_frequency": None,
            },
        ),
    ],
)
def test_parameter_component_from_dict_ok(input_d, ref):

    if not isinstance(input_d, list):
        input_d = [input_d]

    if isinstance(input_d, list):
        for d in input_d:
            r = Parameter.from_dict(d)

            assert r.variable() == ref["variable"]
            assert r.param() == ref["param"]
            assert r.units() == ref["units"]
            assert r.standard_name() == ref["standard_name"]
            assert r.long_name() == ref["long_name"]
            assert r.chem() == ref.get("chem", None)
            assert r.chem_long_name() == ref.get("chem_long_name", None)
            assert r.wavelength() == ref.get("wavelength", None)
            assert r.wave_direction() == ref.get("wave_direction", None)
            assert r.wave_frequency() == ref.get("wave_frequency", None)


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            [
                {
                    "variable": "t",
                    "units": "K",
                },
                {
                    "param": "t",
                    "units": "K",
                },
            ],
            {
                "variable": "t",
                "param": "t",
                "units": "K",
                "standard_name": None,
                "long_name": None,
                "chem": None,
                "chem_long_name": None,
                "wavelength": None,
                "wave_direction": None,
                "wave_frequency": None,
            },
        ),
        (
            [
                {
                    "param": "aod",
                    "standard_name": "unknown",
                    "long_name": "Aerosol optical depth",
                    "units": "Numeric",
                    "chem": "aer_total",
                    "chem_long_name": "Total aerosol",
                    "wavelength": 550,
                }
            ],
            {
                "variable": "aod",
                "param": "aod",
                "standard_name": "unknown",
                "long_name": "Aerosol optical depth",
                "units": "Numeric",
                "chem": "aer_total",
                "chem_long_name": "Total aerosol",
                "wavelength": 550,
                "wave_direction": None,
                "wave_frequency": None,
            },
        ),
        (
            [
                {
                    "variable": "2dfd",
                    "units": "meter ** 2 * second / radian",
                    "standard_name": "unknown",
                    "long_name": "2D wave spectra (single)",
                    "wave_direction": 5.0,
                    "wave_frequency": 0.034523,
                }
            ],
            {
                "variable": "2dfd",
                "param": "2dfd",
                "standard_name": "unknown",
                "long_name": "2D wave spectra (single)",
                "units": "meter ** 2 * second / radian",
                "chem": None,
                "chem_long_name": None,
                "wavelength": None,
                "wave_direction": 5.0,
                "wave_frequency": 0.034523,
            },
        ),
    ],
)
def test_parameter_component_set(input_d, ref):

    r = Parameter(variable="p", units="Pa")

    if not isinstance(input_d, list):
        input_d = [input_d]

    for d in input_d:
        r1 = r.set(**d)

        for k, v in ref.items():
            rv = getattr(r1, k)()
            assert rv == v, f"key {k} expected {v} got {rv}"

        # the original object is unchanged
        assert r.variable() == "p"
        assert r.units() == "Pa"


def test_parameter_component_wavelength_tuple():
    """Test wavelength as a tuple (wavelength range)."""
    p = OpticalParameter(variable="aod", wavelength=(400, 700))
    assert p.wavelength() == (400, 700)


def test_parameter_component_create_parameter_regular():
    """Test create_parameter returns a Parameter for regular parameters."""
    p = create_parameter({"variable": "t", "units": "K"})
    assert isinstance(p, Parameter)
    assert p.variable() == "t"
    assert p.units() == "K"
    assert p.chem() is None
    assert p.wavelength() is None
    assert p.wave_direction() is None
    assert p.wave_frequency() is None


def test_parameter_component_create_parameter_chemical():
    """Test create_parameter returns a ChemicalParameter for chemical parameters."""
    p = create_parameter({"variable": "co", "units": "kg/kg", "chem": "carbon_monoxide", "chem_long_name": "CO"})
    assert isinstance(p, ChemicalParameter)
    assert p.variable() == "co"
    assert p.chem() == "carbon_monoxide"
    assert p.chem_long_name() == "CO"
    assert p.wavelength() is None
    assert p.wave_direction() is None


def test_parameter_component_create_parameter_optical():
    """Test create_parameter returns an OpticalParameter for optical parameters."""
    p = create_parameter({"variable": "aod", "units": "Numeric", "wavelength": 550})
    assert isinstance(p, OpticalParameter)
    assert p.variable() == "aod"
    assert p.wavelength() == 550
    assert p.chem() is None


def test_parameter_component_create_parameter_chemical_optical():
    """Test create_parameter returns a ChemicalOpticalParameter for chemical-optical parameters."""
    p = create_parameter({
        "variable": "aod",
        "units": "Numeric",
        "chem": "aer_total",
        "chem_long_name": "Total aerosol",
        "wavelength": 550,
    })
    assert isinstance(p, ChemicalOpticalParameter)
    assert p.variable() == "aod"
    assert p.chem() == "aer_total"
    assert p.chem_long_name() == "Total aerosol"
    assert p.wavelength() == 550
    assert p.wave_direction() is None


def test_parameter_component_create_parameter_wave_spectra():
    """Test create_parameter returns a WaveSpectraParameter for wave spectra parameters."""
    p = create_parameter({
        "variable": "2dfd",
        "units": "m**2 s / rad",
        "wave_direction": 5.0,
        "wave_frequency": 0.034523,
    })
    assert isinstance(p, WaveSpectraParameter)
    assert p.variable() == "2dfd"
    assert p.wave_direction() == 5.0
    assert p.wave_frequency() == 0.034523
    assert p.chem() is None
    assert p.wavelength() is None


def test_parameter_component_set_changes_type():
    """Test that set() can change the parameter type."""
    p = Parameter(variable="t", units="K")
    assert isinstance(p, Parameter)

    # Add chem -> becomes ChemicalParameter
    p2 = p.set(variable="co", chem="carbon_monoxide")
    assert isinstance(p2, ChemicalParameter)
    assert p2.chem() == "carbon_monoxide"

    # Add wavelength to chem -> becomes ChemicalOpticalParameter
    p3 = p2.set(wavelength=550)
    assert isinstance(p3, ChemicalOpticalParameter)
    assert p3.chem() == "carbon_monoxide"
    assert p3.wavelength() == 550


def test_parameter_component_inheritance():
    """Test that subclasses have the correct inheritance relationships."""
    cp = ChemicalParameter(variable="co", chem="co")
    op = OpticalParameter(variable="aod", wavelength=550)
    cop = ChemicalOpticalParameter(variable="aod", chem="aer", wavelength=550)
    wp = WaveSpectraParameter(variable="2dfd", wave_direction=5.0)

    # All are instances of Parameter
    assert isinstance(cp, Parameter)
    assert isinstance(op, Parameter)
    assert isinstance(cop, Parameter)
    assert isinstance(wp, Parameter)

    # ChemicalOpticalParameter is both Chemical and Optical
    assert isinstance(cop, ChemicalParameter)
    assert isinstance(cop, OpticalParameter)

    # But not cross-contaminated
    assert not isinstance(cp, OpticalParameter)
    assert not isinstance(op, ChemicalParameter)
    assert not isinstance(wp, ChemicalParameter)
    assert not isinstance(wp, OpticalParameter)
