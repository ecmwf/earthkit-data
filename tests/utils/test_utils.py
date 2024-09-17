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

from earthkit.data.utils import ensure_iterable
from earthkit.data.utils import ensure_sequence


@pytest.mark.parametrize(
    "data,expected",
    [("a", ["a"]), ([1], [1]), ((1,), (1,)), (1, [1]), ({"a": 1}, {"a": 1})],
)
def test_utils_ensure_iterable(data, expected):
    assert ensure_iterable(data) == expected


@pytest.mark.parametrize(
    "data,expected",
    [
        ("a", ["a"]),
        ("abc", ["abc"]),
        ([1], [1]),
        ((1,), (1,)),
        (1, [1]),
        ({"a": 1}, [{"a": 1}]),
    ],
)
def test_utils_ensure_sequence(data, expected):
    assert ensure_sequence(data) == expected, f"{data=} {expected=}"


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
