#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Tests for GribParameterContextCollector.collect_keys covering
chem, wavelength, wave_direction_index, and wave_frequency_index context keys.
"""

import pytest
from grib_fixtures import FL_FILE, load_grib_data  # noqa: E402

from earthkit.data.field.component.parameter import (
    ChemicalOpticalParameter,
    ChemicalParameter,
    OpticalParameter,
    Parameter,
    WaveSpectraParameter,
)
from earthkit.data.field.grib.parameter import GribParameterContextCollector
from earthkit.data.field.handler.parameter import ParameterFieldComponentHandler


def _make_handler(component):
    """Helper to wrap a parameter component in a handler."""
    return ParameterFieldComponentHandler(component)


def _collect(handler):
    """Run collect_keys and return the resulting context dict."""
    context = {}
    GribParameterContextCollector.collect_keys(handler, context)
    return context


# --------------------------------------------------------------------------
# Unit tests using constructed components (no file I/O)
# --------------------------------------------------------------------------


class TestCollectKeysBasicParameter:
    """Test collect_keys with a basic Parameter (no chem, wavelength, or wave)."""

    def test_shortname_only(self):
        comp = Parameter(variable="t")
        ctx = _collect(_make_handler(comp))
        assert ctx == {"shortName": "t"}

    def test_no_chem_key(self):
        comp = Parameter(variable="msl", units="Pa")
        ctx = _collect(_make_handler(comp))
        assert "chemShortName" not in ctx

    def test_no_wavelength_keys(self):
        comp = Parameter(variable="msl")
        ctx = _collect(_make_handler(comp))
        assert "firstWavelength" not in ctx
        assert "secondWavelength" not in ctx

    def test_no_direction_frequency_keys(self):
        comp = Parameter(variable="msl")
        ctx = _collect(_make_handler(comp))
        assert "directionNumber" not in ctx
        assert "frequencyNumber" not in ctx


class TestCollectKeysChemParameter:
    """Test collect_keys with ChemicalParameter."""

    def test_chem_short_name_set(self):
        comp = ChemicalParameter(variable="tcvimd", chem="CO")
        ctx = _collect(_make_handler(comp))
        assert ctx["shortName"] == "tcvimd"
        assert ctx["chemShortName"] == "CO"

    def test_chem_with_long_name(self):
        comp = ChemicalParameter(variable="mass_mixrat", chem="O3", chem_long_name="Ozone")
        ctx = _collect(_make_handler(comp))
        assert ctx["chemShortName"] == "O3"
        # chem_long_name is not collected into context
        assert "chemLongName" not in ctx

    def test_chem_none_not_set(self):
        """When chem is None, chemShortName should not appear in context."""
        comp = ChemicalParameter(variable="foo", chem=None)
        ctx = _collect(_make_handler(comp))
        assert "chemShortName" not in ctx

    def test_chem_empty_string_not_set(self):
        """When chem is empty string (falsy), chemShortName should not appear."""
        comp = ChemicalParameter(variable="foo", chem="")
        ctx = _collect(_make_handler(comp))
        assert "chemShortName" not in ctx


class TestCollectKeysOpticalParameter:
    """Test collect_keys with OpticalParameter."""

    def test_wavelength_no_bounds(self):
        """Single wavelength (no bounds) → only firstWavelength set, converted to metres."""
        # wavelength=550 nm → 550e-9 m
        comp = OpticalParameter(variable="aod", wavelength=550, wavelength_units="nm")
        ctx = _collect(_make_handler(comp))
        assert "firstWavelength" in ctx
        assert "secondWavelength" not in ctx
        # 550 nm = 5.5e-7 m
        assert abs(ctx["firstWavelength"] - 5.5e-7) < 1e-12

    def test_wavelength_with_bounds(self):
        """When wavelength_bounds are present, firstWavelength and secondWavelength set."""
        comp = OpticalParameter(
            variable="aod",
            wavelength=625,
            wavelength_bounds=(500, 750),
            wavelength_units="nm",
        )
        ctx = _collect(_make_handler(comp))
        assert "firstWavelength" in ctx
        assert "secondWavelength" in ctx
        # 500 nm = 5e-7 m
        assert abs(ctx["firstWavelength"] - 5e-7) < 1e-12
        # 750 nm = 7.5e-7 m
        assert abs(ctx["secondWavelength"] - 7.5e-7) < 1e-12

    def test_no_direction_frequency_for_optical(self):
        """Optical parameters should not set direction/frequency keys."""
        comp = OpticalParameter(variable="aod", wavelength=550, wavelength_units="nm")
        ctx = _collect(_make_handler(comp))
        assert "directionNumber" not in ctx
        assert "frequencyNumber" not in ctx


class TestCollectKeysChemOpticalParameter:
    """Test collect_keys with ChemicalOpticalParameter."""

    def test_both_chem_and_wavelength(self):
        comp = ChemicalOpticalParameter(
            variable="aod",
            chem="SO4",
            wavelength=550,
            wavelength_bounds=(400, 700),
            wavelength_units="nm",
        )
        ctx = _collect(_make_handler(comp))
        assert ctx["shortName"] == "aod"
        assert ctx["chemShortName"] == "SO4"
        assert "firstWavelength" in ctx
        assert "secondWavelength" in ctx
        assert abs(ctx["firstWavelength"] - 4e-7) < 1e-12
        assert abs(ctx["secondWavelength"] - 7e-7) < 1e-12

    def test_chem_optical_no_bounds(self):
        comp = ChemicalOpticalParameter(
            variable="aod",
            chem="dust",
            wavelength=800,
            wavelength_units="nm",
        )
        ctx = _collect(_make_handler(comp))
        assert ctx["chemShortName"] == "dust"
        assert "firstWavelength" in ctx
        assert "secondWavelength" not in ctx
        assert abs(ctx["firstWavelength"] - 8e-7) < 1e-12


class TestCollectKeysWaveSpectraParameter:
    """Test collect_keys with WaveSpectraParameter."""

    def test_direction_index_converted_to_1_based(self):
        """wave_direction_index is 0-based, directionNumber should be 1-based."""
        comp = WaveSpectraParameter(
            variable="2dfd",
            wave_direction=55.0,
            wave_direction_index=0,
            wave_direction_units="degree",
            wave_frequency=0.035,
            wave_frequency_index=0,
            wave_frequency_units="s ** -1",
        )
        ctx = _collect(_make_handler(comp))
        assert ctx["directionNumber"] == 1

    def test_frequency_index_converted_to_1_based(self):
        """wave_frequency_index is 0-based, frequencyNumber should be 1-based."""
        comp = WaveSpectraParameter(
            variable="2dfd",
            wave_direction=115.0,
            wave_direction_index=2,
            wave_direction_units="degree",
            wave_frequency=0.131,
            wave_frequency_index=5,
            wave_frequency_units="s ** -1",
        )
        ctx = _collect(_make_handler(comp))
        assert ctx["directionNumber"] == 3
        assert ctx["frequencyNumber"] == 6

    def test_direction_only(self):
        """If only direction index is set, only directionNumber appears."""
        comp = WaveSpectraParameter(
            variable="2dfd",
            wave_direction=175.0,
            wave_direction_index=4,
            wave_direction_units="degree",
        )
        ctx = _collect(_make_handler(comp))
        assert ctx["directionNumber"] == 5
        assert "frequencyNumber" not in ctx

    def test_frequency_only(self):
        """If only frequency index is set, only frequencyNumber appears."""
        comp = WaveSpectraParameter(
            variable="2dfd",
            wave_frequency=0.5,
            wave_frequency_index=9,
            wave_frequency_units="s ** -1",
        )
        ctx = _collect(_make_handler(comp))
        assert "directionNumber" not in ctx
        assert ctx["frequencyNumber"] == 10

    def test_no_chem_or_wavelength_for_wave(self):
        """Wave spectra params should not set chem/wavelength keys."""
        comp = WaveSpectraParameter(
            variable="2dfd",
            wave_direction=55.0,
            wave_direction_index=0,
            wave_direction_units="degree",
            wave_frequency=0.035,
            wave_frequency_index=0,
            wave_frequency_units="s ** -1",
        )
        ctx = _collect(_make_handler(comp))
        assert "chemShortName" not in ctx
        assert "firstWavelength" not in ctx
        assert "secondWavelength" not in ctx


# --------------------------------------------------------------------------
# Integration tests using real GRIB data files
# --------------------------------------------------------------------------


@pytest.mark.parametrize("fl_type", FL_FILE)
class TestCollectKeysFromChemGrib:
    """Integration: context collection from chem GRIB files."""

    def test_chem_context(self, fl_type):
        ds, _ = load_grib_data("chem-cams.grib", fl_type, folder="data")
        expected_chems = ["CO", "HCHO", "O3"]
        for i, chem in enumerate(expected_chems):
            f = ds[i]
            handler = f._components["parameter"]
            ctx = _collect(handler)
            assert ctx["shortName"] == f.parameter.variable()
            assert ctx["chemShortName"] == chem
            assert "firstWavelength" not in ctx
            assert "secondWavelength" not in ctx
            assert "directionNumber" not in ctx
            assert "frequencyNumber" not in ctx


@pytest.mark.parametrize("fl_type", FL_FILE)
class TestCollectKeysFromOpticalGrib:
    """Integration: context collection from optical GRIB files."""

    def test_optical_context_wavelength(self, fl_type):
        ds, _ = load_grib_data("optical-cams.grib", fl_type, folder="data")
        for f in ds:
            handler = f._components["parameter"]
            ctx = _collect(handler)
            assert "firstWavelength" in ctx
            # wavelength in metres
            wl_m = f.parameter.wavelength(units="m")
            assert abs(ctx["firstWavelength"] - wl_m) < 1e-15
            assert "directionNumber" not in ctx
            assert "frequencyNumber" not in ctx


@pytest.mark.parametrize("fl_type", FL_FILE)
class TestCollectKeysFromWaveSpectraGrib:
    """Integration: context collection from wave spectra GRIB files."""

    def test_wave_direction_number(self, fl_type):
        ds, _ = load_grib_data("wave_spectra.grib", fl_type, folder="data")
        for f in ds:
            handler = f._components["parameter"]
            ctx = _collect(handler)
            # directionNumber should be 1-based
            expected = f.parameter.wave_direction_index() + 1
            assert ctx["directionNumber"] == expected

    def test_wave_frequency_number(self, fl_type):
        ds, _ = load_grib_data("wave_spectra.grib", fl_type, folder="data")
        for f in ds:
            handler = f._components["parameter"]
            ctx = _collect(handler)
            # frequencyNumber should be 1-based
            expected = f.parameter.wave_frequency_index() + 1
            assert ctx["frequencyNumber"] == expected

    def test_wave_no_chem_or_wavelength(self, fl_type):
        ds, _ = load_grib_data("wave_spectra.grib", fl_type, folder="data")
        f = ds[0]
        handler = f._components["parameter"]
        ctx = _collect(handler)
        assert "chemShortName" not in ctx
        assert "secondWavelength" not in ctx
