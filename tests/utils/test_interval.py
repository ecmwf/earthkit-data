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

from earthkit.data.utils.humanize import interval_to_human
from earthkit.data.utils.interval import Interval


@pytest.mark.parametrize("_kwargs", [{}, {"closed": "both"}])
def test_interval(_kwargs):
    v = Interval(1, 2, **_kwargs)
    assert 0 not in v
    assert 1 in v
    assert 1.5 in v
    assert 2 in v
    assert 3 not in v


def test_interval_closed_left():
    v = Interval(1, 2, closed="left")
    assert 0 not in v
    assert 1 in v
    assert 1.5 in v
    assert 2 not in v
    assert 3 not in v


def test_interval_closed_right():
    v = Interval(1, 2, closed="right")
    assert 0 not in v
    assert 1 not in v
    assert 1.5 in v
    assert 2 in v
    assert 3 not in v


def test_interval_closed_none():
    v = Interval(1, 2, closed="none")
    assert 0 not in v
    assert 1 not in v
    assert 1.5 in v
    assert 2 not in v
    assert 3 not in v


def test_interval_bounded_left():
    v = Interval(1, None)
    assert 0 not in v
    assert 1 in v
    assert 2 in v


def test_interval_bounded_right():
    v = Interval(None, 2)
    assert 1 in v
    assert 2 in v
    assert 3 not in v


def test_interval_unbounded():
    v = Interval(None, None)
    assert 1 in v
    assert 2 in v
    assert "a" in v


def test_interval_invalid():
    with pytest.raises(ValueError):
        Interval(2, 1)

    with pytest.raises(ValueError):
        Interval(1, 1)

    with pytest.raises(ValueError):
        Interval(2, 1, closed="all")

    with pytest.raises(TypeError):
        Interval("b", 2)


def test_interval_humanised():
    v = Interval(1, 2)
    assert interval_to_human(v) == "1 <= x <= 2"

    v = Interval(1, 2, closed="both")
    assert interval_to_human(v) == "1 <= x <= 2"

    v = Interval(1, 2, closed="left")
    assert interval_to_human(v) == "1 <= x < 2"

    v = Interval(1, 2, closed="right")
    assert interval_to_human(v) == "1 < x <= 2"

    v = Interval(1, 2, closed="none")
    assert interval_to_human(v) == "1 < x < 2"

    v = Interval(None, 2, closed="both")
    assert interval_to_human(v) == "x <= 2"

    v = Interval(None, 2, closed="left")
    assert interval_to_human(v) == "x < 2"

    v = Interval(None, 2, closed="right")
    assert interval_to_human(v) == "x <= 2"

    v = Interval(None, 2, closed="none")
    assert interval_to_human(v) == "x < 2"

    v = Interval(1, None, closed="both")
    assert interval_to_human(v) == "x >= 1"

    v = Interval(1, None, closed="left")
    assert interval_to_human(v) == "x >= 1"

    v = Interval(1, None, closed="right")
    assert interval_to_human(v) == "x > 1"

    v = Interval(1, None, closed="none")
    assert interval_to_human(v) == "x > 1"

    v = Interval(None, None)
    assert interval_to_human(v) == ""


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
