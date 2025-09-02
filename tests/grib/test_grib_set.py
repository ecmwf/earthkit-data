#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
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
def test_grib_set_parameter(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    def _func1(field, key, original_metadata):
        return original_metadata.get(key) + "a"

    def _func2(field, key, original_metadata):
        return "kg/kg"

    f = ds_ori[0].set(name="q", units="kg/kg")
    assert f.get("name") == "q"
    assert f.get("param") == "q"
    assert f.get("shortName") == "t"
    assert f.get("units") == "kg/kg"

    f = ds_ori[0].set(param="q", units="kg/kg")
    assert f.get("name") == "q"
    assert f.get("param") == "q"
    assert f.get("shortName") == "t"
    assert f.get("units") == "kg/kg"

    f = ds_ori[0].set(name=_func1, units=_func2)
    assert f.get("name") == "ta"
    assert f.get("param") == "ta"
    assert f.get("shortName") == "t"
    assert f.get("units") == "kg/kg"


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
def test_grib_set_vertical(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    def _func1(field, key, original_metadata):
        return original_metadata.get(key) + 300

    def _func2(field, key, original_metadata):
        return "theta"

    f = ds_ori[0].set(level=700, level_type="ml")
    assert f.get("level") == 700
    assert f.get("levelist") == 700
    assert f.get("level_type") == "ml"

    assert ds_ori[0].get("level") == 500
    assert ds_ori[0].get("level_type") == "pl"

    f = ds_ori[0].set(levelist=700, level_type="ml")
    assert f.get("level") == 700
    assert f.get("levelist") == 700
    assert f.get("level_type") == "ml"


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
# @pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
@pytest.mark.parametrize(
    "_kwargs",
    [
        {"base_datetime": "2025-08-24T12:00:00", "step": 6},
        {"base_datetime": datetime.datetime(2025, 8, 24, 12), "step": datetime.timedelta(hours=6)},
        {"valid_datetime": "2025-08-24T18:00:00", "step": datetime.timedelta(hours=6)},
        {"valid_datetime": datetime.datetime(2025, 8, 24, 18), "step": datetime.timedelta(hours=6)},
    ],
)
def test_grib_set_time_1(fl_type, write_method, _kwargs):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)
    assert f.get("base_datetime") == datetime.datetime(2025, 8, 24, 12)
    assert f.get("valid_datetime") == datetime.datetime(2025, 8, 24, 18)
    assert f.get("step") == datetime.timedelta(hours=6)
    assert f.get("step_range") == datetime.timedelta(hours=0)

    assert ds_ori[0].get("base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("step") == datetime.timedelta(hours=0)
    assert ds_ori[0].get("step_range") == datetime.timedelta(hours=0)


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
@pytest.mark.parametrize(
    "_kwargs",
    [
        {"base_datetime": "2025-08-24T12:00:00"},
        {"base_datetime": datetime.datetime(2025, 8, 24, 12)},
        {"valid_datetime": "2025-08-24T12:00:00"},
        {"valid_datetime": datetime.datetime(2025, 8, 24, 12)},
    ],
)
def test_grib_set_time_2(fl_type, write_method, _kwargs):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)
    assert f.get("base_datetime") == datetime.datetime(2025, 8, 24, 12)
    assert f.get("valid_datetime") == datetime.datetime(2025, 8, 24, 12)
    assert f.get("step") == datetime.timedelta(hours=0)
    assert f.get("step_range") == datetime.timedelta(hours=0)

    assert ds_ori[0].get("base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("step") == datetime.timedelta(hours=0)
    assert ds_ori[0].get("step_range") == datetime.timedelta(hours=0)


@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
@pytest.mark.parametrize(
    "_kwargs",
    [
        {
            "latitudes": np.array([10.0, 20.0, 30.0]),
            "longitudes": np.array([0.0, 10.0, 20.0]),
            "values": np.array([1.0, 2.0, 3.0]),
        },
    ],
)
def test_grib_set_geo(fl_type, write_method, _kwargs):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)
    assert np.allclose(f.get("latitudes"), np.array([10.0, 20.0, 30.0]))
    assert np.allclose(f.get("longitudes"), np.array([0.0, 10.0, 20.0]))
    assert np.allclose(f.values, np.array([1.0, 2.0, 3.0]))
    assert f.get("base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert f.get("valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert f.get("step") == datetime.timedelta(hours=0)
    assert f.get("step_range") == datetime.timedelta(hours=0)

    assert ds_ori[0].get("base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("step") == datetime.timedelta(hours=0)
    assert ds_ori[0].get("step_range") == datetime.timedelta(hours=0)


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
def test_grib_set_data(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    f = ds_ori[0].set(values=vals_ori + 1)

    assert f.get("param") == "t"
    assert f.get("shortName") == "t"
    assert f.get("level") == 500
    assert f.get("levelist") == 500
    assert f.get("date", "param") == (20070101, "t")
    assert f.get("param", "date") == ("t", 20070101)
    assert np.allclose(f.values, vals_ori + 1)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.get("param") == "t"
        assert f_saved.get("shortName") == "t"
        assert f_saved.get("level") == 500
        assert f_saved.get("levelist") == 500
        assert np.allclose(f_saved.values, vals_ori + 1)

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].set(values=vals_ori + 1)
    f = f.set(values=vals_ori + 2)

    assert f.get("param") == "t"
    assert f.get("shortName") == "t"
    assert f.get("level") == 500
    assert f.get("levelist") == 500
    assert f.get("date", "param") == (20070101, "t")
    assert f.get("param", "date") == ("t", 20070101)
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

    assert ds.get("param") == ["t", "z"]
    assert ds.get("shortName") == ["t", "z"]
    assert ds.get("level") == [500, 500]
    assert ds.get("levelist") == [500, 500]
    assert np.allclose(ds[0].values, vals_ori + 1)
    assert np.allclose(ds[1].values, vals_ori + 2)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.get("param") == ["t", "z"]
        assert ds_saved.get("shortName") == ["t", "z"]
        assert ds_saved.get("level") == [500, 500]
        assert ds_saved.get("levelist") == [500, 500]
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


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
def test_grib_set_detailed(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    def _func1(field, key, original_metadata):
        return original_metadata.get(key) + 100

    def _func2(field, key, original_metadata):
        return field.shape

    def _func3(field, key, original_metadata):
        return original_metadata.get("param") + "_" + str(original_metadata.get("levelist"))

    def _func4(field, key, original_metadata):
        return original_metadata.get(key) + 200

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
        levelist=_func1,
        my_shape=_func2,
        my_name=_func3,
    )

    assert f.get("param") == "q"
    assert f.get("shortName") == "t"
    assert f.get("level") == 600
    assert f.get("levelist") == 600
    assert f.get("date", "param") == (20070101, "q")
    assert f.get("param", "date") == ("q", 20070101)
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
            level=_func1,
        )

        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.get("param") == "q"
        assert f_saved.get("shortName") == "q"
        assert f_saved.get("level") == 600
        assert f_saved.get("levelist") == 600
        assert f_saved.get("grib.level") == 600
        assert f_saved.get("grib.levelist") == 600
        assert f_saved.get("level_type") == "pl"
        assert f_saved.get("typeOfLevel") == "isobaricInhPa"

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].set(
        param="q",
        levelist=_func1,
        my_shape=_func2,
        my_name=_func3,
    )

    f = f.set(param="pt", levelist=_func4)

    assert f.get("param") == "pt"
    assert f.get("shortName") == "t"
    assert f.get("grib.shortName") == "t"
    assert f.get("level") == 800
    assert f.get("levelist") == 800
    assert f.get("grib.level") == 500
    assert f.get("grib.levelist") == 500

    # TODO: this should be 800
    # assert f.metadata("levelist") == 700
    assert f.get("date", "param") == (20070101, "pt")
    assert f.get("param", "date") == ("pt", 20070101)
    # assert np.allclose(np.array(f.metadata("mars_area")), np.array([90.0, 0.0, -90.0, 359.0]))
    assert f.get("my_name") == "t_500"

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        f = ds_ori[i].set(
            param="q",
            levelist=_func1,
        )
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.get("param") == ["q", "q"]
    assert ds.get("shortName") == ["t", "z"]
    assert ds.get("level") == [600, 600]
    assert ds.get("levelist") == [600, 600]

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.get("param") == ["q", "q"]
        assert ds_saved.get("shortName") == ["q", "q"]
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

    def _func1(field, key, original_metadata):
        return original_metadata.get(key) + 100

    def _func2(field, key, original_metadata):
        return original_metadata.get(key) + 200

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].set(
        values=vals_ori + 1,
        param="q",
        levelist=_func1,
    )

    assert f.get("param") == "q"
    assert f.get("shortName") == "t"
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

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].set(
        values=vals_ori + 1,
        param="q",
        levelist=_func1,
    )
    f = f.set(values=vals_ori + 2, param="pt", levelist=_func2)

    assert f.get("param") == "pt"
    assert f.get("shortName") == "t"
    assert f.get("level") == 800
    assert f.get("levelist") == 800
    assert f.get("date", "param") == (20070101, "pt")
    assert f.get("param", "date") == ("pt", 20070101)
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
            levelist=_func1,
        )
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.get("param") == ["q", "q"]
    assert ds.get("shortName") == ["t", "z"]
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
    assert f.get("shortName") == "t"
    assert f.get("level") == 500
    assert f.get("levelist") == 500
    assert f.get("date", "param") == (20070101, "t")
    assert f.get("param", "date") == ("t", 20070101)
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
