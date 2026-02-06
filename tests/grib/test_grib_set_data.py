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
import sys

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.indexing.fieldlist import FieldList
from earthkit.data.testing import write_to_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
def test_grib_set_data(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    f = ds_ori[0].set(values=vals_ori + 1)

    assert f.get("parameter.variable") == "t"
    assert f.get("metadata.shortName") == "t"
    assert f.get("vertical.level") == 500
    assert f.get("metadata.levelist") == 500
    assert f.get("metadata.date", "parameter.variable") == (20070101, "t")
    assert f.get("parameter.variable", "metadata.date") == ("t", 20070101)
    assert np.allclose(f.values, vals_ori + 1)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.get("parameter.variable") == "t"
        assert f_saved.get("metadata.shortName") == "t"
        assert f_saved.get("vertical.level") == 500
        assert f_saved.get("metadata.levelist") == 500
        assert np.allclose(f_saved.values, vals_ori + 1)

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].set(values=vals_ori + 1)
    f = f.set(values=vals_ori + 2)

    assert f.get("parameter.variable") == "t"
    assert f.get("metadata.shortName") == "t"
    assert f.get("vertical.level") == 500
    assert f.get("metadata.levelist") == 500
    assert f.get("metadata.date", "parameter.variable") == (20070101, "t")
    assert f.get("parameter.variable", "metadata.date") == ("t", 20070101)
    assert np.allclose(f.values, vals_ori + 2)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        f = ds_ori[i].set(values=vals_ori + i + 1)
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.get("parameter.variable") == ["t", "z"]
    assert ds.get("metadata.shortName") == ["t", "z"]
    assert ds.get("vertical.level") == [500, 500]
    assert ds.get("metadata.levelist") == [500, 500]
    assert np.allclose(ds[0].values, vals_ori + 1)
    assert np.allclose(ds[1].values, vals_ori + 2)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.get("parameter.variable") == ["t", "z"]
        assert ds_saved.get("metadata.shortName") == ["t", "z"]
        assert ds_saved.get("vertical.level") == [500, 500]
        assert ds_saved.get("metadata.levelist") == [500, 500]
        assert np.allclose(ds_saved[0].values, vals_ori + 1)
        assert np.allclose(ds_saved[1].values, vals_ori + 2)

    # TODO: implement the following
    # serialise
    # pickled_f = pickle.dumps(ds)
    # ds_1 = pickle.loads(pickled_f)

    # assert ds_1.metadata("param") == ["q", "q"]
    # assert ds_1.metadata("shortName") == ["q", "q"]
    # assert ds_1.metadata("level") == [600, 600]
    # assert ds_1.metadata("levelist") == [600, 600]
