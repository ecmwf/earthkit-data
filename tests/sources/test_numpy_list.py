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

import numpy as np

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.testing import earthkit_examples_file

LOG = logging.getLogger(__name__)


def test_numpy_list_grib():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    v1 = np.array([v1])

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    fs = FieldList.from_numpy(v1, md1)

    assert len(fs) == 1
    assert np.allclose(v1, fs[0].values)
    assert fs[0].shape == ds[0].shape
    assert fs[0].metadata("shortName") == "msl"


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
