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
import logging

import pytest

from earthkit.data import from_object

LOG = logging.getLogger(__name__)


def test_string_wrapper():
    v = "hello"
    ds = from_object(v)
    assert ds._TYPE_NAME == "str"
    assert "value" in ds.available_types

    assert ds.to_string() == v
    assert ds.to_value() == v


@pytest.mark.parametrize("date_format, expected_value", [("%Y-%m-%d", "2000-01-01")])
def test_string_wrapper_datetime(date_format, expected_value):

    dt = datetime.datetime(2000, 1, 1)
    v = dt.strftime(date_format)
    ds = from_object(v)
    assert ds._TYPE_NAME == "str"
    assert "datetime" in ds.available_types
    assert ds.to_string() == expected_value
    assert ds.to_datetime() == dt


@pytest.mark.parametrize("date_format,", ["%Y-%m-%d"])
def test_string_wrapper_datetime_list(date_format):
    dt = [datetime.datetime(2000, 1, i) for i in range(1, 30)]

    # Currently not accepted: "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"
    datetime_list_string = "/to/".join([dt[i].strftime(date_format) for i in (0, -1)])
    ds = from_object(datetime_list_string)

    assert ds._TYPE_NAME == "str"
    assert "datetime_list" in ds.available_types
    assert ds.to_value() == datetime_list_string
    assert ds.to_string() == datetime_list_string
    assert ds.to_datetime_list() == dt


@pytest.mark.parametrize("date_format,", ["%Y-%m-%d"])
def test_string_wrapper_datetime_list_by(date_format):
    dt = [datetime.datetime(2000, 1, i) for i in range(1, 30, 2)]

    # Currently not accepted: "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"s:
    datetime_list_string = "/to/".join([dt[i].strftime(date_format) for i in (0, -1)])
    ds = from_object(datetime_list_string + "/by/2")
    assert ds._TYPE_NAME == "str"
    assert "datetime_list" in ds.available_types
    assert ds.to_value() == datetime_list_string + "/by/2"
    assert ds.to_string() == datetime_list_string + "/by/2"
    assert ds.to_datetime_list() == dt
