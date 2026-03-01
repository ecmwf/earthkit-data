#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import sys

import pytest

here = os.path.dirname(__file__)
sys.path.insert(0, here)

from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_kwargs,error",
    [
        ({"labels.my_label": 2}, None),
        ({"labels.my_label_1": 2, "labels.my_label_2": "2"}, None),
        ({"labels.": 2}, KeyError),
        ({"labels": 2}, KeyError),
        ({"my_label": 2}, KeyError),
    ],
)
def test_grib_field_labels_core(fl_type, _kwargs, error):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    f = ds[0]

    if error:
        with pytest.raises(error):
            f1 = f.set(**_kwargs)
        return
    else:
        f1 = f.set(**_kwargs)

    for k, v in _kwargs.items():
        sn = f1.get(k)
        assert sn == v


@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize(
    "_kwargs1,_kwargs2,expected_vales",
    [
        (
            {"labels.my_label": 2},
            {"labels.other_label": 3},
            {"labels.my_label": 2, "labels.other_label": 3},
        ),
        (
            {"labels.my_label": 2},
            {"labels.my_label": 3},
            {"labels.my_label": 3},
        ),
    ],
)
def test_grib_field_labels_1(fl_type, _kwargs1, _kwargs2, expected_vales):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    f = ds[0]

    f1 = f.set(**_kwargs1)
    f2 = f1.set(**_kwargs2)

    for k, v in expected_vales.items():
        r = f2.get(k)
        assert r == v, f"key={k}, value={r}, expected={v}"

    assert len(f2.labels) == len(expected_vales)
