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

from earthkit.data.field.part.ensemble import Ensemble


def test_ensemble_part_alias_1():
    r = Ensemble(member=1)
    assert r.member() == "1"
    assert r.realisation() == "1"
    assert r.realization() == "1"


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            [
                {"member": 5},
                {"realisation": 5},
                {"realization": 5},
                {"member": "5"},
                {"realisation": "5"},
                {"realization": "5"},
            ],
            ("5",),
        ),
    ],
)
def test_ensemble_part_from_dict_ok(input_d, ref):

    if not isinstance(input_d, list):
        input_d = [input_d]

    if isinstance(input_d, list):
        for d in input_d:
            r = Ensemble.from_dict(d)

            assert r.member() == ref[0]
            assert r.realisation() == ref[0]
            assert r.realization() == ref[0]


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            [
                {
                    "member": 4,
                },
                {
                    "realisation": 4,
                },
                {
                    "realization": 4,
                },
                {
                    "member": "4",
                },
                {
                    "realisation": "4",
                },
                {
                    "realization": "4",
                },
            ],
            {
                "member": "4",
                "realisation": "4",
                "realization": "4",
            },
        ),
    ],
)
def test_ensemble_part_set(input_d, ref):

    r = Ensemble(member=5)

    if not isinstance(input_d, list):
        input_d = [input_d]

    for d in input_d:
        r1 = r.set(**d)

        for k, v in ref.items():
            rv = getattr(r1, k)()
            assert rv == v, f"key {k} expected {v} got {rv}"

        # the original object is unchanged
        assert r.member() == "5"
