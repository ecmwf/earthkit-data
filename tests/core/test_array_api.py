#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data import array_api


def test_array_api():
    b = array_api.get_backend("numpy")
    assert b.name == "numpy"

    import numpy as np

    v = np.ones(10)
    assert array_api.get_backend(v) is b
