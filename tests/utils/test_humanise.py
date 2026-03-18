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

from earthkit.data.utils.humanize import did_you_mean


@pytest.mark.parametrize(
    "word,vocabulary,expected",
    [
        ("appl", ["apple", "banana", "orange"], "apple"),
        (
            "banan",
            [
                "banana",
            ],
            "banana",
        ),
        ("orenge", ["apple", "banana", "orange"], "orange"),
    ],
)
def test_did_you_mean_1(word, vocabulary, expected):
    assert did_you_mean(word, vocabulary) == expected


def test_did_you_mean_2():
    vocabulary = []
    with pytest.raises(ValueError):
        did_you_mean("appl", vocabulary)

    vocabulary = None
    with pytest.raises(ValueError):
        did_you_mean("appl", vocabulary)
