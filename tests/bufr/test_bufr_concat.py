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
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_remote_test_data_file


def test_bufr_concat():
    ds1 = from_source("file", earthkit_examples_file("temp_10.bufr"))
    ds2 = from_source("url", earthkit_remote_test_data_file("examples/synop_10.bufr"))
    ds = ds1 + ds2

    assert len(ds) == 20
    md = [x._header("dataCategory") for x in ds1] + [x._header("dataCategory") for x in ds2]
    assert md == [2] * 10 + [0] * 10


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
