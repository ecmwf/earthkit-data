#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime

import pytest

from earthkit.data.decorators import normalize


def f(d):
    return d


@pytest.mark.parametrize(
    "values,expected",
    [
        (datetime.timedelta(hours=6), datetime.timedelta(hours=6)),
        (
            [datetime.timedelta(hours=6), datetime.timedelta(hours=12)],
            [datetime.timedelta(hours=6), datetime.timedelta(hours=12)],
        ),
        (
            (datetime.timedelta(hours=6), datetime.timedelta(hours=12)),
            (datetime.timedelta(hours=6), datetime.timedelta(hours=12)),
        ),
        ("6", datetime.timedelta(hours=6)),
        ("12", datetime.timedelta(hours=12)),
        (["6", "12"], [datetime.timedelta(hours=6), datetime.timedelta(hours=12)]),
        (("6", "12"), (datetime.timedelta(hours=6), datetime.timedelta(hours=12))),
    ],
)
def test_normalize_timedelta(values, expected):
    timedelta_formatted = normalize("d", "timedelta")(f)

    assert timedelta_formatted(values) == expected
