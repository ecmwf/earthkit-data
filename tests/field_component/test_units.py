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

from earthkit.data.utils.units import Units


@pytest.mark.parametrize(
    "input_units,expected_value,pint_object",
    [
        ("m/s", "meter / second", True),
        ("m s-1", "meter / second", True),
        ("m s^-1", "meter / second", True),
        ("m/s2", "meter / second ** 2", True),
        ("invalid", "invalid", False),
    ],
)
def test_units_to_str(input_units, expected_value, pint_object):
    r = Units.from_any(input_units)
    assert str(r) == expected_value
    if pint_object:
        assert r.to_pint() is not None
    else:
        assert r.to_pint() is None


@pytest.mark.parametrize(
    "units",
    [["m/s", "m s-1", "m s**-1"], ["degC", "celsius"], ["K", "kelvin"], ["(0 - 1)", "percent", "%"]],
)
def test_units_equal(units):
    units = [Units.from_any(u) for u in units]

    first = units[0]
    for u in units[1:]:
        assert u == first
        assert u.to_pint() == first.to_pint()
        assert u.to_pint() is not None
        assert str(u) == str(first)
