#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from datetime import timedelta

import numpy as np
import pytest

from earthkit.data.utils.dates import numpy_timedelta_to_timedelta
from earthkit.data.utils.dates import step_to_delta
from earthkit.data.utils.dates import step_to_grib


@pytest.mark.parametrize(
    "step,expected_delta,error",
    [
        (12, timedelta(hours=12), None),
        ("12h", timedelta(hours=12), None),
        ("12s", timedelta(seconds=12), None),
        ("12m", timedelta(minutes=12), None),
        ("1m", timedelta(minutes=1), None),
        ("", None, ValueError),
        ("m", None, ValueError),
        ("1Z", None, ValueError),
        ("m1", None, ValueError),
        ("-1", None, ValueError),
        ("-1s", None, ValueError),
        ("1.1s", None, ValueError),
    ],
)
def test_step_to_delta(step, expected_delta, error):
    if error is None:
        assert step_to_delta(step) == expected_delta
    else:
        with pytest.raises(error):
            step_to_delta(step)


@pytest.mark.parametrize(
    "td,expected_delta,error",
    [
        (np.timedelta64(61, "s"), timedelta(minutes=1, seconds=1), None),
        (np.timedelta64((2 * 3600 + 61) * 1000, "ms"), timedelta(hours=2, minutes=1, seconds=1), None),
        (
            np.timedelta64((2 * 3600 + 61) * 1000 * 1000 * 1000, "ns"),
            timedelta(hours=2, minutes=1, seconds=1),
            None,
        ),
    ],
)
def test_numpy_timedelta_to_timedelta(td, expected_delta, error):
    if error is None:
        assert numpy_timedelta_to_timedelta(td) == expected_delta
    else:
        with pytest.raises(error):
            numpy_timedelta_to_timedelta(td)


@pytest.mark.parametrize(
    "step,expected_value,error",
    [
        (0, 0, None),
        (6, 6, None),
        (12, 12, None),
        (120, 120, None),
        ("0h", "0h", None),
        ("6h", "6h", None),
        ("12h", "12h", None),
        ("120h", "120h", None),
        ("6m", "6m", None),
        ("6s", "6s", None),
        (np.timedelta64(6, "h"), 6, None),
        (np.timedelta64(6 * 3600 * 1000, "ms"), 6, None),
        (np.timedelta64(6 * 3600 * 1000 * 1000 * 1000, "ns"), 6, None),
        (np.timedelta64(61, "s"), "61s", None),
        (np.timedelta64((2 * 3600 + 61) * 1000, "ms"), "7261s", None),
        (
            np.timedelta64((2 * 3600 + 61) * 1000 * 1000 * 1000, "ns"),
            "7261s",
            None,
        ),
    ],
)
def test_step_to_grib(step, expected_value, error):
    if error is None:
        assert step_to_grib(step) == expected_value
    else:
        with pytest.raises(error):
            step_to_grib(step)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
