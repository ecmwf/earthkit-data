#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging

from earthkit.data import from_object
from earthkit.data import wrappers
from earthkit.data.wrappers import string as strwrapper

LOG = logging.getLogger(__name__)


def test_string_wrapper():
    _wrapper = strwrapper.wrapper(" ")
    assert isinstance(_wrapper, strwrapper.StrWrapper)
    _wrapper = wrappers.get_wrapper(" ")
    assert isinstance(_wrapper, strwrapper.StrWrapper)
    _wrapper = from_object(" ")
    assert isinstance(_wrapper, strwrapper.StrWrapper)


def test_datetime_string():
    import datetime

    _datetime = datetime.datetime(2000, 1, 1)
    date_formats = ["%Y-%m-%d"]
    # Currently not accepted: "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"
    for d_format in date_formats:
        _wrapper = strwrapper.wrapper(_datetime.strftime(d_format))
        assert _datetime == _wrapper.datetime()


def test_datetime_list_string():
    import datetime

    _datetime_list = [datetime.datetime(2000, 1, i) for i in range(1, 30)]
    date_formats = ["%Y-%m-%d"]
    # Currently not accepted: "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"
    for d_format in date_formats:
        datetime_list_string = "/to/".join([_datetime_list[i].strftime(d_format) for i in (0, -1)])
        _wrapper = strwrapper.wrapper(datetime_list_string)
        assert _datetime_list == _wrapper.to_datetime_list()


def test_datetime_list_string_by():
    import datetime

    _datetime_list = [datetime.datetime(2000, 1, i) for i in range(1, 30, 2)]
    date_formats = ["%Y-%m-%d"]
    # Currently not accepted: "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"
    for d_format in date_formats:
        datetime_list_string = "/to/".join([_datetime_list[i].strftime(d_format) for i in (0, -1)])
        _wrapper = strwrapper.wrapper(datetime_list_string + "/by/2")
        assert _datetime_list == _wrapper.to_datetime_list()


def test_boundingbox_string():
    import datetime

    _datetime_list = [datetime.datetime(2000, 1, i) for i in range(1, 30, 2)]
    date_formats = ["%Y-%m-%d"]
    # Currently not accepted: "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"
    for d_format in date_formats:
        datetime_list_string = "/to/".join([_datetime_list[i].strftime(d_format) for i in (0, -1)])
        _wrapper = strwrapper.wrapper(datetime_list_string + "/by/2")
        assert _datetime_list == _wrapper.to_datetime_list()
