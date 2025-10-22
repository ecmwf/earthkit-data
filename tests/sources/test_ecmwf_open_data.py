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

from earthkit.data import from_source
from earthkit.data.testing import NO_EOD

YESTERDAY = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")

REQ_1 = dict(
    param="t",
    levelist=500,
    date=YESTERDAY,
)

REQ_2 = dict(
    param="r",
    levelist=500,
    date=YESTERDAY,
)


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
def test_eod_single_1():
    ds = from_source(
        "ecmwf-open-data",
        param=["2t", "msl"],
        levtype="sfc",
    )
    assert len(ds) == 2
    assert ds.metadata("param") == ["2t", "msl"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
@pytest.mark.parametrize(
    "_args,req,_kwargs",
    [
        ((REQ_1,), None, {}),
        (([REQ_1]), None, {}),
        ((), REQ_1, {}),
        ((), [REQ_1], {}),
        ((), None, REQ_1),
    ],
)
def test_eod_single_2(_args, req, _kwargs):
    ds = from_source(
        "ecmwf-open-data",
        *_args,
        request=req,
        **_kwargs,
    )
    assert len(ds) == 1
    assert ds[0].metadata(["param", "level"]) == ["t", 500]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.parametrize("_args,req,_kwargs", [((REQ_1, REQ_2), None, {}), ((), [REQ_1, REQ_2], {})])
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
def test_eod_multi_1(_args, req, _kwargs):
    ds = from_source(
        "ecmwf-open-data",
        *_args,
        request=req,
        **_kwargs,
    )
    assert len(ds) == 2
    assert ds.metadata("param") == ["t", "r"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
@pytest.mark.parametrize("model", ["ifs"])  # "aifs" does not seem to work
def test_eod_model(model):
    ds = from_source(
        "ecmwf-open-data",
        model=model,
        param="t",
        date=YESTERDAY,
        levelist=500,
    )
    assert len(ds) == 1
    assert ds[0].metadata(["param", "level"]) == ["t", 500]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
