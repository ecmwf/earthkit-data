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

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.testing import earthkit_examples_file

# Note: All grib metadata tests are also run for numpyfs.
# See grib/test_grib_metadata.py


def test_numpy_fs_grib_values_metadata():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    v = ds[0].values
    v_new = v + 1
    md_new = ds[0].metadata().override(generatingProcessIdentifier=150)

    ds_new = FieldList.from_numpy(v_new, md_new)

    # values metadata
    keys = ["min", "max"]
    for k in keys:
        assert np.isclose(ds_new[0].metadata(k), ds[0].metadata(k) + 1)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
