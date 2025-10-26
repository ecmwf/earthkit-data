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
    "_kwargs",
    [
        ({"my_label": 2}),
        ({"my_label_1": 2, "my_label_2": "2"}),
    ],
)
def test_grib_field_labels(fl_type, _kwargs):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    f = ds[0]
    f1 = f.set(**_kwargs)

    for k, v in _kwargs.items():
        sn = f1.get(k)
        assert sn == v
