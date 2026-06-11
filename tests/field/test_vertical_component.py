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

from earthkit.data.field.component.level_parameters import HybridLevelParameters
from earthkit.data.field.component.level_type import get_level_type
from earthkit.data.field.component.vertical import ParametricVertical, Vertical

A = (0.1, 0.2, 0.3, 0.4)
B = (0.4, 0.5, 0.6, 0.7)
hybrid_params = HybridLevelParameters(A=A, B=B)


def test_vertical_component_alias_1():
    r = Vertical(level=1000, level_type="pressure")
    assert r.level() == 1000
    assert r.level_type() == "pressure"


def test_vertical_component_convert_level_units():
    r = Vertical(level=1000, level_type="pressure")
    assert r.level() == 1000
    assert r.level_type() == "pressure"

    # convert to Pa
    level_pa = r.level(units="Pa")
    assert level_pa == 100000

    level_hpa = r.level(units="hPa")
    assert level_hpa == 1000


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            {
                "level": 1000,
                "level_type": "pressure",
            },
            {
                "level": 1000,
                "level_type": "pressure",
                "number_of_levels": None,
                "coefficients": None,
            },
        ),
        (
            {
                "level": 1000,
                "level_type": "pressure",
            },
            {
                "level": 1000,
                "level_type": "pressure",
                "number_of_levels": None,
                "coefficients": None,
            },
        ),
        (
            {
                "level": 2,
                "level_type": "hybrid",
                "coefficients": (A, B),
            },
            {
                "level": 2,
                "level_type": "hybrid",
                "number_of_levels": 3,
                "coefficients": (A, B),
            },
        ),
        (
            {
                "level": 2,
                "level_type": "hybrid",
                "coefficients": hybrid_params,
            },
            {
                "level": 2,
                "level_type": "hybrid",
                "number_of_levels": 3,
                "coefficients": (A, B),
            },
        ),
    ],
)
def test_vertical_component_from_dict_ok(input_d, ref):
    if not isinstance(input_d, list):
        input_d = [input_d]

    if isinstance(input_d, list):
        for d in input_d:
            r = Vertical.from_dict(d)

            assert r.level() == ref["level"]
            assert r.level_type() == ref["level_type"]
            assert r.number_of_levels() == ref.get("number_of_levels")
            assert r.coefficients() == ref.get("coefficients")


def test_vertical_component_type():
    r = Vertical(level=1000, level_type="pressure")

    t = r._type
    assert t == "pressure"
    assert t.name == "pressure"
    assert t.abbreviation == "pl"
    assert t.units == "hPa"
    assert t.positive == "down"
    assert t.cf == {
        "standard_name": "air_pressure",
        "long_name": "pressure",
        "units": "hectopascal",
        "positive": "down",
    }
    assert t.parametric is False
    assert t.coefficient_names is None

    assert r.level() == 1000
    assert r.level_type() == "pressure"
    assert r.abbreviation() == "pl"
    assert r.units() == "hPa"
    assert r.positive() == "down"
    assert r.cf() == {
        "standard_name": "air_pressure",
        "long_name": "pressure",
        "units": "hectopascal",
        "positive": "down",
    }
    assert r.parametric() is False
    assert r.number_of_levels() is None
    assert r.coefficient_names() is None

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
                {"level": 500, "level_type": "pressure"},
            ],
            {
                "level": 500,
                "layer": None,
                "level_type": "pressure",
            },
        ),
        (
            [
                {"level": 320, "level_type": "potential_temperature"},
            ],
            {"level": 320, "level_type": "potential_temperature"},
        ),
    ],
)
def test_vertical_component_set_1(input_d, ref):
    r = Vertical(level=1000, level_type="pressure")

    if not isinstance(input_d, list):
        input_d = [input_d]

    for d in input_d:
        r1 = r.set(**d)

        for k, v in ref.items():
            rv = getattr(r1, k)()
            assert rv == v, f"key {k} expected {v} got {rv}"

        # the original object is unchanged
        assert r.level() == 1000
        assert r.level_type() == "pressure"


def test_vertical_component_set_hybrid_1():
    r = ParametricVertical(level=1, level_type="hybrid", coefficients=(A, B))

    r1 = r.set({"level": 2})

    assert r1.level() == 2
    assert r1.level_type() == "hybrid"
    assert r1.number_of_levels() == 3
    A1, B1 = r1.coefficients()
    assert A1 == A
    assert B1 == B


def test_vertical_component_set_hybrid_2():
    r = ParametricVertical(level=1, level_type="hybrid", coefficients=(A, B))

    A_new = (0.15, 0.25, 0.35, 0.45, 0.55)
    B_new = (0.45, 0.55, 0.65, 0.75, 0.85)
    r1 = r.set({"level": 2}, coefficients=(A_new, B_new))

    assert r1.level() == 2
    assert r1.level_type() == "hybrid"
    assert r1.number_of_levels() == 4
    A1, B1 = r1.coefficients()
    assert A1 == A_new
    assert B1 == B_new


def test_vertical_component_register():
    r = Vertical(level=1000, level_type="_my_level_type")

    assert r.level() == 1000
    assert r.level_type() == "_my_level_type"
