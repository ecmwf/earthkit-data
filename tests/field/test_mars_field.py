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

from earthkit.data.field.mars.create import create_mars_field


def test_mars_field_core():
    mars_request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": 0,
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    f = create_mars_field(mars_request)

    assert f.get("parameter.variable") == "z"
    assert f.get("time.base_datetime") == datetime.datetime(2020, 12, 21, 12, 0)
    assert f.get("time.valid_datetime") == datetime.datetime(2020, 12, 21, 12, 0)
    assert f.get("time.step") == datetime.timedelta(0)
    assert f.get("vertical.level") == 1000
    assert f.get("vertical.level_type") == "pressure"

    assert f.get("labels.mars") == mars_request


def test_mars_field_step():
    mars_request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": 6,
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    f = create_mars_field(mars_request)

    assert f.get("parameter.variable") == "z"
    assert f.get("time.base_datetime") == datetime.datetime(2020, 12, 21, 12, 0)
    assert f.get("time.valid_datetime") == datetime.datetime(2020, 12, 21, 18, 0)
    assert f.get("time.step") == datetime.timedelta(hours=6)
    assert f.get("vertical.level") == 1000
    assert f.get("vertical.level_type") == "pressure"

    assert f.get("labels.mars") == mars_request


def test_mars_field_hdate():
    mars_request = {
        "class": "od",
        "date": "20231221",
        "hdate": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": 6,
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    f = create_mars_field(mars_request)

    assert f.get("parameter.variable") == "z"
    assert f.get("time.base_datetime") == datetime.datetime(2020, 12, 21, 12, 0)
    assert f.get("time.valid_datetime") == datetime.datetime(2020, 12, 21, 18, 0)
    assert f.get("time.step") == datetime.timedelta(hours=6)
    assert f.get("vertical.level") == 1000
    assert f.get("vertical.level_type") == "pressure"

    assert f.get("labels.mars") == mars_request
