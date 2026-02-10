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

from earthkit.data.field.component.level_type import get_level_type
from earthkit.data.field.component.vertical import Vertical


def test_vertical_component_alias_1():
    r = Vertical(level=1000, type="pressure")
    assert r.level() == 1000
    assert r.type() == "pressure"


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            {
                "level": 1000,
                "type": "pressure",
            },
            (1000, "pressure"),
        ),
        (
            {
                "level": 1000,
                "type": "pressure",
            },
            (1000, "pressure"),
        ),
    ],
)
def test_vertical_component_from_dict_ok(input_d, ref):

    if not isinstance(input_d, list):
        input_d = [input_d]

    if isinstance(input_d, list):
        for d in input_d:
            r = Vertical.from_dict(d)

            assert r.level() == ref[0]
            assert r.type() == "pressure"


def test_vertical_component_type():
    r = Vertical(level=1000, type="pressure")

    t = r._type
    assert t == "pressure"
    assert t.name == "pressure"
    assert t.abbreviation == "pl"
    assert t.units == "hPa"
    assert t.positive == "down"
    assert t.cf == {"standard_name": "air_pressure", "long_name": "pressure"}

    assert r.level() == 1000
    assert r.type() == "pressure"
    assert r.abbreviation() == "pl"
    assert r.units() == "hPa"
    assert r.positive() == "down"
    assert r.cf() == {"standard_name": "air_pressure", "long_name": "pressure"}

    p_type = get_level_type("pressure")
    assert p_type == t
    assert p_type == "pressure"


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            [
                {
                    "level": 500,
                },
                {"level": 500, "type": "pressure"},
            ],
            {
                "level": 500,
                "layer": None,
                "type": "pressure",
            },
        ),
        (
            [
                {"level": 320, "type": "potential_temperature"},
            ],
            {"level": 320, "type": "potential_temperature"},
        ),
    ],
)
def test_vertical_component_set(input_d, ref):

    r = Vertical(level=1000, type="pressure")

    if not isinstance(input_d, list):
        input_d = [input_d]

    for d in input_d:
        r1 = r.set(**d)

        for k, v in ref.items():
            rv = getattr(r1, k)()
            assert rv == v, f"key {k} expected {v} got {rv}"

        # the original object is unchanged
        assert r.level() == 1000
        assert r.type() == "pressure"
