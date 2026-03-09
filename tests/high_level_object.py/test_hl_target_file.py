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
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.encoders.grib import GribEncoder
from earthkit.data.targets import to_target
from earthkit.data.utils.testing import earthkit_examples_file


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"encoder": "grib"},
        {"encoder": GribEncoder()},
    ],
)
@pytest.mark.parametrize("direct_call", [True, False])
def test_hl_target_file_grib_core_non_stream(kwargs, direct_call):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.to_fieldlist().values[:, :4]

    with temp_file() as path:
        if direct_call:
            to_target("file", path, data=ds, **kwargs)
        else:
            ds.to_target("file", path, **kwargs)

        ds1 = from_source("file", path).to_fieldlist()
        assert ds1.get("parameter.variable") == ["2t", "msl"]
        assert ds1.get("metadata.shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)
