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

from earthkit.data.field.component.parameter import Parameter


def test_parameter_component_alias_1():
    r = Parameter(variable="t", units="K")
    assert r.variable() == "t"
    assert r.param() == "t"
    assert r.units() == "K"
    assert r.standard_name() is None
    assert r.long_name() is None


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
