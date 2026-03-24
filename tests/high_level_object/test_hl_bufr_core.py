#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_examples_file


def test_hl_bufr_single_core():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"))

    assert ds._TYPE_NAME == "BUFR"
    assert ds.is_stream() is False
    assert "featurelist" in ds.available_types

    fl = ds.to_featurelist()
    assert len(fl) == 10
    assert fl.get("dataCategory") == [2] * 10


def test_hl_bufr_multi_core():
    paths = [earthkit_examples_file("temp_10.bufr"), earthkit_examples_file("synop_10.bufr")]
    ds = from_source("file", paths)

    assert ds._TYPE_NAME == "BUFR"
    assert ds.is_stream() is False
    assert "featurelist" in ds.available_types

    fl = ds.to_featurelist()
    assert len(fl) == 20
    assert fl.get("dataCategory") == [2] * 10 + [0] * 10
