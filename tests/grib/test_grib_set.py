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
from earthkit.data.sources.array_list import ArrayField
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import write_to_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
def test_grib_set_detailed(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    # ---------------
    # field
    # ---------------

    # f = ds_ori[0].clone(
    #     param="q",
    #     levelist=_func1,
    #     mars_area=_func2,
    #     name=_func3,
    # )

    f = ds_ori[0].set(
        param="q",
        levelist=600,
        my_shape=(181, 360),
        my_name="t_500",
    )

    assert f.get("param") == "q"
    assert f.get("grib.shortName") == "t"
    assert f.get("level") == 600
    assert f.get("levelist") == 600
    assert f.get("grib.date", "param") == (20070101, "q")
    assert f.get("param", "grib.date") == ("q", 20070101)
    assert f.get("my_shape") == (181, 360)
    assert f.get("my_name") == "t_500"

    # TODO: apply wrapped metadata to namespaces
    # assert f.get(namespace="mars") == {
    #     "class": "ea",
    #     "date": 20070101,
    #     "domain": "g",
    #     "expver": "0001",
    #     "levelist": 500,
    #     "levtype": "pl",
    #     "param": "t",
    #     "step": 0,
    #     "stream": "oper",
    #     "time": 1200,
    #     "type": "an",
    # }

    # write back to grib
    with temp_file() as tmp:
        f = ds_ori[0].set(
            param="q",
            level=600,
        )

        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.get("param") == "q"
        assert f_saved.get("grib.shortName") == "q"
        assert f_saved.get("level") == 600
        assert f_saved.get("levelist") == 600
        assert f_saved.get("grib.level") == 600
        assert f_saved.get("grib.levelist") == 600
        assert f_saved.get("level_type") == "pl"
        assert f_saved.get("grib.typeOfLevel") == "isobaricInhPa"

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].set(
        param="q",
        levelist=600,
        my_shape=(181, 360),
        my_name="t_500",
    )

    f = f.set(param="pt", levelist=800)

    assert f.get("param") == "pt"
    assert f.get("grib.shortName") == "t"
    assert f.get("level") == 800
    assert f.get("levelist") == 800
    assert f.get("grib.level") == 500
    assert f.get("grib.levelist") == 500

    # TODO: this should be 800
    # assert f.metadata("levelist") == 700
    assert f.get("grib.date", "param") == (20070101, "pt")
    assert f.get("param", "grib.date") == ("pt", 20070101)
    # assert np.allclose(np.array(f.metadata("mars_area")), np.array([90.0, 0.0, -90.0, 359.0]))
    assert f.get("my_name") == "t_500"

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        f = ds_ori[i].set(
            param="q",
            levelist=600,
        )
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.get("param") == ["q", "q"]
    assert ds.get("grib.shortName") == ["t", "z"]
    assert ds.get("level") == [600, 600]
    assert ds.get("levelist") == [600, 600]

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.get("param") == ["q", "q"]
        assert ds_saved.get("grib.shortName") == ["q", "q"]
        assert ds_saved.get("level") == [600, 600]
        assert ds_saved.get("levelist") == [600, 600]

    # TODO: implement the following
    # serialise
    # pickled_f = pickle.dumps(ds)
    # ds_1 = pickle.loads(pickled_f)

    # assert ds_1.metadata("param") == ["q", "q"]
    # assert ds_1.metadata("shortName") == ["q", "q"]
    # assert ds_1.metadata("level") == [600, 600]
    # assert ds_1.metadata("levelist") == [600, 600]


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize("write_method", ["target"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_set_combined(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].set(
        values=vals_ori + 1,
        param="q",
        levelist=600,
    )

    assert f.get("param") == "q"
    assert f.get("grib.shortName") == "t"
    assert f.get("level") == 600
    assert f.get("levelist") == 600
    assert f.get("grib.date", "param") == (20070101, "q")
    assert f.get("param", "grib.date") == ("q", 20070101)
    assert np.allclose(f.values, vals_ori + 1)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.get("param") == "q"
        assert f_saved.get("grib.shortName") == "q"
        assert f_saved.get("level") == 600
        assert f_saved.get("levelist") == 600
        assert np.allclose(f_saved.values, vals_ori + 1)

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].set(
        values=vals_ori + 1,
        param="q",
        levelist=600,
    )
    f = f.set(values=vals_ori + 2, param="pt", levelist=800)

    assert f.get("param") == "pt"
    assert f.get("grib.shortName") == "t"
    assert f.get("level") == 800
    assert f.get("levelist") == 800
    assert f.get("grib.date", "param") == (20070101, "pt")
    assert f.get("param", "grib.date") == ("pt", 20070101)
    assert np.allclose(f.values, vals_ori + 2)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        f = ds_ori[i].set(
            values=vals_ori + i + 1,
            param="q",
            levelist=600,
        )
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.get("param") == ["q", "q"]
    assert ds.get("grib.shortName") == ["t", "z"]
    assert ds.get("level") == [600, 600]
    assert ds.get("levelist") == [600, 600]
    assert np.allclose(ds[0].values, vals_ori + 1)
    assert np.allclose(ds[1].values, vals_ori + 2)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.get("param") == ["q", "q"]
        assert ds_saved.get("grib.shortName") == ["q", "q"]
        assert ds_saved.get("level") == [600, 600]
        assert ds_saved.get("levelist") == [600, 600]
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


@pytest.mark.skip(reason="Not sure if it will ever be implemented")
@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_set_default(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].set()

    assert f.get("param") == "t"
    assert f.get("grib.shortName") == "t"
    assert f.get("level") == 500
    assert f.get("levelist") == 500
    assert f.get("grib.date", "param") == (20070101, "t")
    assert f.get("param", "grib.date") == ("t", 20070101)
    assert np.allclose(f.values, vals_ori)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.get("param") == "t"
        assert f_saved.get("shortName") == "t"
        assert f_saved.get("level") == 500
        assert f_saved.get("levelist") == 500
        assert np.allclose(f_saved.values, vals_ori)


@pytest.mark.skip(reason="Not sure if it will ever be implemented")
@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_set_with_metadata_object(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    md = ds_ori[0].metadata().override(shortName="q", level=600)

    f = ds_ori[0].set(metadata=md)

    assert f.get("param") == "q"
    assert f.get("shortName") == "q"
    assert f.get("level") == 600
    assert f.get("levelist") == 600
    assert f.get("date", "param") == (20070101, "q")
    assert f.get("param", "date") == ("q", 20070101)
    assert np.allclose(f.values, vals_ori)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.get("param") == "q"
        assert f_saved.get("shortName") == "q"
        assert f_saved.get("level") == 600
        assert f_saved.get("levelist") == 600
        assert np.allclose(f_saved.values, vals_ori)

    with pytest.raises(ValueError):
        ds_ori[0].set(metadata=md, param="q")


@pytest.mark.skip(reason="Not sure if it will ever be implemented")
@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_copy_to_field(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    # ---------------
    # field
    # ---------------

    md = (
        ds_ori[0]
        .metadata()
        .override(
            shortName="q",
            level=600,
        )
    )

    f = ds_ori[0].copy(
        values=vals_ori + 1,
        metadata=md,
    )

    assert isinstance(f, ArrayField)
    assert f.get("param") == "q"
    assert f.get("shortName") == "q"
    assert f.get("level") == 600
    assert f.get("levelist") == 600
    assert f.get("date", "param") == (20070101, "q")
    assert f.get("param", "date") == ("q", 20070101)
    assert np.allclose(f.values, vals_ori + 1)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.get("param") == "q"
        assert f_saved.get("shortName") == "q"
        assert f_saved.get("level") == 600
        assert f_saved.get("levelist") == 600
        assert np.allclose(f_saved.values, vals_ori + 1)

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        md = (
            ds_ori[i]
            .metadata()
            .override(
                shortName="q",
                level=600,
            )
        )
        f = ds_ori[i].copy(
            values=vals_ori + i + 1,
            metadata=md,
        )
        assert isinstance(f, ArrayField)
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.get("param") == ["q", "q"]
    assert ds.get("shortName") == ["q", "q"]
    assert ds.get("level") == [600, 600]
    assert ds.get("levelist") == [600, 600]
    assert np.allclose(ds[0].values, vals_ori + 1)
    assert np.allclose(ds[1].values, vals_ori + 2)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.get("param") == ["q", "q"]
        assert ds_saved.get("shortName") == ["q", "q"]
        assert ds_saved.get("level") == [600, 600]
        assert ds_saved.get("levelist") == [600, 600]
        assert np.allclose(ds_saved[0].values, vals_ori + 1)
        assert np.allclose(ds_saved[1].values, vals_ori + 2)
