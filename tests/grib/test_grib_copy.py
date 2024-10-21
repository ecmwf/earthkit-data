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

from earthkit.data import FieldList
from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
def test_grib_copy_core(fl_type):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    def _func1(field, key, original_metadata):
        return original_metadata[key] + 100

    def _func2(field, key, original_metadata):
        return field.mars_area

    def _func3(field, key, original_metadata):
        return original_metadata.get("param") + "_" + str(original_metadata.get("levelist"))

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].copy(
        param="q",
        levelist=_func1,
        mars_area=_func2,
        name=_func3,
    )

    assert f.metadata("param") == "q"
    assert f.metadata("shortName") == "t"
    assert f.metadata("level") == 500
    assert f.metadata("levelist") == 600
    assert f.metadata("date", "param") == (20070101, "q")
    assert f.metadata("param", "date") == ("q", 20070101)
    assert np.allclose(np.array(f.metadata("mars_area")), np.array([90.0, 0.0, -90.0, 359.0]))
    assert f.metadata("name") == "t_500"

    # TODO: apply wrapped metadata to namespaces
    assert f.metadata(namespace="mars") == {
        "class": "ea",
        "date": 20070101,
        "domain": "g",
        "expver": "0001",
        "levelist": 500,
        "levtype": "pl",
        "param": "t",
        "step": 0,
        "stream": "oper",
        "time": 1200,
        "type": "an",
    }

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        f = ds_ori[0].copy(
            param="q",
            levelist=_func1,
        )

        f.save(tmp)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.metadata("param") == "q"
        assert f_saved.metadata("shortName") == "q"
        assert f_saved.metadata("level") == 600
        assert f_saved.metadata("levelist") == 600

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        f = ds_ori[i].copy(
            param="q",
            levelist=_func1,
        )
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.metadata("param") == ["q", "q"]
    assert ds.metadata("shortName") == ["t", "z"]
    assert ds.metadata("level") == [500, 500]
    assert ds.metadata("levelist") == [600, 600]

    # write back to grib
    with temp_file() as tmp:
        ds.save(tmp)
        ds_saved = from_source("file", tmp)
        assert ds_saved.metadata("param") == ["q", "q"]
        assert ds_saved.metadata("shortName") == ["q", "q"]
        assert ds_saved.metadata("level") == [600, 600]
        assert ds_saved.metadata("levelist") == [600, 600]

    # TODO: implement the following
    # serialise
    # pickled_f = pickle.dumps(ds)
    # ds_1 = pickle.loads(pickled_f)

    # assert ds_1.metadata("param") == ["q", "q"]
    # assert ds_1.metadata("shortName") == ["q", "q"]
    # assert ds_1.metadata("level") == [600, 600]
    # assert ds_1.metadata("levelist") == [600, 600]
