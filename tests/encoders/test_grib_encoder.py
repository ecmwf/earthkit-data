#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import numpy as np

from earthkit.data import create_encoder, from_source
from earthkit.data.utils.testing import earthkit_examples_file


def test_grib_encoder():
    f = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()[0]

    encoder = create_encoder("grib")
    r = encoder.encode(f)

    assert r.to_bytes() == f.message()

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() == f_r.message()
    assert np.allclose(f.values, f_r.values)
    assert f.get("parameter.variable") == f_r.get("parameter.variable")
