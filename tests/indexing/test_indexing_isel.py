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
from indexing_fixtures import check_sel_and_order, get_fixtures  # noqa: E402


@pytest.mark.parametrize(
    "params,levels,source_name",
    [
        (
            ({"value": ["t", "u"], "index": [0, 1]}),
            ({"value": [500, 850], "index": [3, 5]}),
            "directory",
        ),
        (
            ({"value": ["t", "u"], "index": [0, 1]}),
            ({"value": [500, 850], "index": [0, 1]}),
            "list-of-dicts",
        ),
        (
            ({"value": ["t", "u"], "index": [0, 1]}),
            ({"value": [500, 850], "index": [3, 1]}),
            "file",
        ),
    ],
)
def test_indexing_isel(params, levels, source_name):
    request = dict(param=params["index"], level=levels["index"], date=0, time=0)
    order_by = ["level", "variable"]

    ds, _, total, n = get_fixtures(source_name, {})

    assert len(ds) == total, len(ds)

    ds = ds.isel(**request)
    assert len(ds) == n, len(ds)

    ds = ds.order_by(order_by)

    check_sel_and_order(ds, params["value"], levels["value"])


if __name__ == "__main__":
    from emohawk.testing import main

    main(__file__)
