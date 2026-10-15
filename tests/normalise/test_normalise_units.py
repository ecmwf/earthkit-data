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
from earthkit.utils.units import Units

from earthkit.data.decorators import normalise


def f(d):
    return d


@pytest.mark.parametrize(
    "values,expected",
    [
        ("K", Units.from_any("K")),
        ("kelvins", Units.from_any("K")),
        ("K", Units.from_any("kelvins")),
        ("kelvins", Units.from_any("kelvins")),
        (["kelvins", "m/s"], [Units.from_any("kelvins"), Units.from_any("m/s")]),
        (["K", Units.from_any("m/s")], [Units.from_any("K"), Units.from_any("m/s")]),
    ],
)
def test_normalise_units(values, expected):
    units_f = normalise("d", "units")(f)

    assert units_f(values) == expected
