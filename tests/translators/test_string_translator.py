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

from earthkit.data import from_object, transform

LOG = logging.getLogger(__name__)


def test_string_translator():
    val = "Eartha"
    ds = from_object(val)

    assert transform(val, str) == val
    assert transform(ds, str) == val

    assert isinstance(transform(val, str), str)
    assert isinstance(transform(ds, str), str)
