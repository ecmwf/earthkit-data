#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import pickle
import sys

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize("array_backend", ["numpy"])
def test_grib_serialise_metadata(fl_type, array_backend):
    ds = load_grib_data("test.grib", fl_type, array_backend)

    md = ds[0].metadata().override()
    pickled_md = pickle.dumps(md)
    md2 = pickle.loads(pickled_md)

    keys = ["param", "date", "time", "step", "level", "gridType", "type"]
    for k in keys:
        assert md[k] == md2[k]


@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize("array_backend", ["numpy"])
def test_grib_serialise_array_field(fl_type, array_backend):
    ds0 = load_grib_data("test.grib", fl_type, array_backend)
    ds = ds0.to_fieldlist()

    for idx in range(len(ds)):
        pickled_f = pickle.dumps(ds[0])
        f2 = pickle.loads(pickled_f)

        assert np.allclose(ds[0].values, f2.values), f"index={idx}"
        assert np.allclose(ds[0].to_numpy(), f2.to_numpy()), f"index={idx}"

        keys = ["param", "date", "time", "step", "level", "gridType", "type"]
        for k in keys:
            assert ds[0].metadata(k) == f2.metadata(k), f"index={idx}"


@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize("array_backend", ["numpy"])
def test_grib_serialise_array_fieldlist(fl_type, array_backend):
    ds0 = load_grib_data("test.grib", fl_type, array_backend)
    ds = ds0.to_fieldlist()

    pickled_f = pickle.dumps(ds)
    ds2 = pickle.loads(pickled_f)

    assert len(ds) == len(ds2)
    assert np.allclose(ds.values, ds2.values)

    keys = ["param", "date", "time", "step", "level", "gridType", "type"]
    for k in keys:
        ds.metadata(k) == ds.metadata(k)

    r = ds2.sel(param="2t")
    assert len(r) == 1

    ds2[0]._array += 1
    v1 = ds[0]._array

    with temp_file() as tmp:
        ds2.save(tmp)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp, array_backend=array_backend)
        assert len(ds2) == len(r_tmp)
        v_tmp = r_tmp[0].to_numpy()
        assert np.allclose(v1 + 1, v_tmp)
