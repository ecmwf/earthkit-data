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
from grib_fixtures import (
    FL_FILE,  # noqa: E402
    load_grib_data,  # noqa: E402
)

from earthkit.data.readers.grib.handle import GribCodesHandle


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_message_core(fl_type):
    f, _ = load_grib_data("test.grib", fl_type)
    v = f[0].message()
    assert len(v) == 316
    assert v[:4] == b"GRIB"
    v = f[1].message()
    assert len(v) == 316
    assert v[:4] == b"GRIB"


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_message_change_values(fl_type):
    f, _ = load_grib_data("test.grib", fl_type)
    m = f[0].message()
    handle = GribCodesHandle.from_message(m)
    assert handle.get("shortName") == "2t"

    # modify the values
    f1 = f[0].set(values=f[0].values + 1)
    m1 = f1.message()
    assert m1[:4] == b"GRIB"
    handle1 = GribCodesHandle.from_message(m1)
    assert handle1.get("shortName") == "2t"
    assert np.allclose(handle1.get_values(), f[0].values + 1)

    # the original field/handle is not modified
    assert np.allclose(f[0].values, handle.get_values())
    assert np.allclose(handle.get_values(), f[0].values)


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_message_change_values_and_metadata(fl_type):
    f, _ = load_grib_data("test.grib", fl_type)
    m = f[0].message()
    handle = GribCodesHandle.from_message(m)
    assert handle.get("shortName") == "2t"

    # modify the values and the metadata. The grib handle in the field
    # becomes out of sync with the field metadata, and the message cannot be generated.
    f1 = f[0].set({"parameter.variable": "msl"}, values=f[0].values + 1)
    m1 = f1.message()
    assert m1 is None

    # the handle is no longer valid
    assert f1._get_grib(strict=True) is None

    # the original handle is still kept, but we need to use strict=False to get
    #  it, as the metadata is now inconsistent with the handle
    md = f1._get_grib(strict=False)
    assert md is not None
    assert md.get("shortName") == "2t"
    assert np.allclose(md.handle.get_values(), f[0].values)
