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

from earthkit.data.utils.request import RequestBuilder


def normaliser_func(**r):
    return r


REQ_1 = dict(
    variable=["2t", "msl"],
    product_type="reanalysis",
    area=[50, -50, 20, 50],
    date="2012-12-12",
    time="00:00",
)

REQ_2 = dict(
    variable=["2t", "msl"],
    product_type="reanalysis",
    area=[50, -50, 20, 50],
    date="2012-12-12",
    time="12:00",
)

REQ_3 = dict(
    variable=["2t", "msl", "tp"],
    product_type="reanalysis",
    area=[50, -50, 20, 50],
    date="2012-12-12",
    time=["00:00", "12:00"],
)

REQ_4 = dict(
    variable=["t", "r"],
    product_type="reanalysis",
    area=[50, -50, 20, 50],
    date="2012-12-12",
    time=["06:00", "18:00"],
)


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
def test_utils_request_single_1(_args, req, _kwargs):

    retriever = RequestBuilder("A", *_args, request=req, normaliser=normaliser_func, **_kwargs)
    assert retriever.requests == [REQ_1]


@pytest.mark.parametrize(
    "_args,req,_kwargs",
    [
        ((REQ_1,), None, {"time": "06:00", "step": 6}),
        (([REQ_1]), None, {"time": "06:00", "step": 6}),
        ((), REQ_1, {"time": "06:00", "step": 6}),
        ((), [REQ_1], {"time": "06:00", "step": 6}),
    ],
)
def test_utils_request_single_2(_args, req, _kwargs):
    ref = REQ_1.copy()
    ref.update(_kwargs)

    retriever = RequestBuilder("A", *_args, request=req, normaliser=normaliser_func, **_kwargs)
    assert retriever.requests == [ref]


def test_utils_request_single_3():
    def _normaliser_func(**r):
        r["time"] = "0"
        return r

    ref = REQ_1.copy()
    ref["time"] = "0"

    retriever = RequestBuilder("A", REQ_1, normaliser=_normaliser_func)
    assert retriever.requests == [ref]


@pytest.mark.parametrize(
    "split_on,ref",
    [
        (
            "variable",
            [
                dict(
                    variable=("2t",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("msl",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("tp",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
            ],
        ),
        (
            ("variable",),
            [
                dict(
                    variable=("2t",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("msl",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("tp",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
            ],
        ),
        (
            {"variable": 1},
            [
                dict(
                    variable=("2t",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("msl",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("tp",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
            ],
        ),
        (
            {"variable": 2},
            [
                dict(
                    variable=("2t", "msl"),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("tp",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
            ],
        ),
        (
            ("variable", "time"),
            [
                dict(
                    variable=("2t",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("00:00",),
                ),
                dict(
                    variable=("2t",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("12:00",),
                ),
                dict(
                    variable=("msl",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("00:00",),
                ),
                dict(
                    variable=("msl",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("12:00",),
                ),
                dict(
                    variable=("tp",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("00:00",),
                ),
                dict(
                    variable=("tp",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("12:00",),
                ),
            ],
        ),
        (
            {"variable": 2, "time": 2},
            [
                dict(
                    variable=("2t", "msl"),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("00:00", "12:00"),
                ),
                dict(
                    variable=("tp",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("00:00", "12:00"),
                ),
            ],
        ),
    ],
)
def test_utils_request_single_split_on_1(split_on, ref):
    req = REQ_3.copy()
    req["split_on"] = split_on

    retriever = RequestBuilder("A", req, normaliser=normaliser_func)
    assert retriever.requests == ref


@pytest.mark.parametrize(
    "split_on_1,split_on_2,ref",
    [
        (
            "variable",
            "variable",
            [
                dict(
                    variable=("2t",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("msl",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("tp",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("t",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["06:00", "18:00"],
                ),
                dict(
                    variable=("r",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["06:00", "18:00"],
                ),
            ],
        ),
        (
            "variable",
            "time",
            [
                dict(
                    variable=("2t",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("msl",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=("tp",),
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=["00:00", "12:00"],
                ),
                dict(
                    variable=["t", "r"],
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("06:00",),
                ),
                dict(
                    variable=["t", "r"],
                    product_type="reanalysis",
                    area=[50, -50, 20, 50],
                    date="2012-12-12",
                    time=("18:00",),
                ),
            ],
        ),
    ],
)
def test_utils_request_single_split_on_2(split_on_1, split_on_2, ref):
    req_1 = REQ_3.copy()
    req_1["split_on"] = split_on_1

    req_2 = REQ_4.copy()
    req_2["split_on"] = split_on_2

    retriever = RequestBuilder("A", request=[req_1, req_2], normaliser=normaliser_func)
    assert retriever.requests == ref


def test_utils_request_single_invalid():
    with pytest.raises(TypeError):
        RequestBuilder("A", 3, normaliser=normaliser_func)

    with pytest.raises(TypeError):
        RequestBuilder("A", "a", normaliser=normaliser_func)

    with pytest.raises(TypeError):
        RequestBuilder("A", [3], normaliser=normaliser_func)

    with pytest.raises(TypeError):
        RequestBuilder("A", (3,), normaliser=normaliser_func)


@pytest.mark.parametrize(
    "_args,req,_kwargs",
    [
        ((REQ_1, REQ_2), None, {"time": "06:00", "step": 6}),
        (([REQ_1, REQ_2]), None, {}),
        ((), [REQ_1, REQ_2], {}),
        ((REQ_2,), [REQ_1], {}),
        (([REQ_2],), [REQ_1], {}),
    ],
)
def test_utils_request_multi_1(_args, req, _kwargs):
    retriever = RequestBuilder("A", *_args, request=req, normaliser=normaliser_func, **_kwargs)

    assert retriever.requests == [REQ_1, REQ_2]
