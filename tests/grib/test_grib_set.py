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
from grib_fixtures import load_grib_data  # noqa: E402

from earthkit.data import FieldList, from_source
from earthkit.data.core.temporary import temp_file


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
# @pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_field_detailed_1(fl_type):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set({
        "parameter.variable": "q",
        "vertical.level": 600,
        "labels.my_shape": (181, 360),
        "labels.my_name": "t_500",
    })

    assert f.get("parameter.variable") == "q"
    assert f.get("metadata.shortName") is None
    assert f.get("vertical.level") == 600
    assert f.get("metadata.levelist") is None
    assert f.get(("metadata.date", "parameter.variable")) == (None, "q")
    assert f.get(("parameter.variable", "metadata.date")) == ("q", None)
    assert f.get("labels.my_shape") == (181, 360)
    assert f.get("labels.my_name") == "t_500"

    f1 = f.sync()
    assert f1.get("parameter.variable") == "q"
    assert f1.get("metadata.shortName") == "q"
    assert f1.get("vertical.level") == 600
    assert f1.get("metadata.levelist") == 600
    assert f1.get(("metadata.date", "parameter.variable")) == (20070101, "q")
    assert f1.get(("parameter.variable", "metadata.date")) == ("q", 20070101)
    assert f1.get("labels.my_shape") == (181, 360)
    assert f1.get("labels.my_name") == "t_500"

    # write back to grib
    with temp_file() as tmp:
        f = ds_ori[0].set({
            "parameter.variable": "q",
            "vertical.level": 600,
        })

        f.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()[0]
        assert f_saved.get("parameter.variable") == "q"
        assert f_saved.get("parameter.variable") == "q"
        assert f_saved.get("metadata.shortName") == "q"
        assert f_saved.get("vertical.level") == 600
        assert f_saved.get("metadata.level") == 600
        assert f_saved.get("metadata.levelist") == 600
        assert f_saved.get("vertical.level_type") == "pressure"
        assert f_saved.get("metadata.typeOfLevel") == "isobaricInhPa"


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
# @pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_field_detailed_2(fl_type):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set({
        "parameter.variable": "q",
        "vertical.level": 600,
        "labels.my_shape": (181, 360),
        "labels.my_name": "t_500",
    })

    f = f.set({
        "parameter.variable": "pt",
        "vertical.level": 800,
    })

    assert f.get("parameter.variable") == "pt"
    assert f.get("metadata.shortName") is None
    assert f.get("vertical.level") == 800
    assert f.get("metadata.level") is None
    assert f.get("metadata.levelist") is None
    assert f.get(("metadata.date", "parameter.variable")) == (None, "pt")
    assert f.get(("parameter.variable", "metadata.date")) == ("pt", None)
    assert f.get("labels.my_name") == "t_500"

    f1 = f.sync()
    assert f1.get("parameter.variable") == "pt"
    assert f1.get("metadata.shortName") == "pt"
    assert f1.get("vertical.level") == 800
    assert f1.get("metadata.level") == 800
    assert f1.get("metadata.levelist") == 800
    assert f1.get("metadata.typeOfLevel") == "isobaricInhPa"
    assert f1.get("vertical.level_type") == "pressure"
    assert f1.get(("metadata.date", "parameter.variable")) == (20070101, "pt")
    assert f1.get(("parameter.variable", "metadata.date")) == ("pt", 20070101)
    assert f1.get("labels.my_name") == "t_500"


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
# @pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_fieldlist_detailed(fl_type):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    fields = []
    for i in range(2):
        f = ds_ori[i].set({
            "parameter.variable": "q",
            "vertical.level": 600,
        })
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.get("parameter.variable") == ["q", "q"]
    assert ds.get("metadata.shortName") == [None, None]
    assert ds.get("vertical.level") == [600, 600]
    assert ds.get("metadata.levelist") == [None, None]

    # write back to grib
    with temp_file() as tmp:
        ds.to_target("file", tmp)
        ds_saved = from_source("file", tmp).to_fieldlist()
        assert ds_saved.get("parameter.variable") == ["q", "q"]
        assert ds_saved.get("metadata.shortName") == ["q", "q"]
        assert ds_saved.get("vertical.level") == [600, 600]
        assert ds_saved.get("metadata.levelist") == [600, 600]

    # TODO: implement the following
    # serialise
    # pickled_f = pickle.dumps(ds)
    # ds_1 = pickle.loads(pickled_f)

    # assert ds_1.metadata("param") == ["q", "q"]
    # assert ds_1.metadata("shortName") == ["q", "q"]
    # assert ds_1.metadata("level") == [600, 600]
    # assert ds_1.metadata("levelist") == [600, 600]x


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
def test_grib_set_combined(fl_type):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].set({
        "values": vals_ori + 1,
        "parameter.variable": "q",
        "vertical.level": 600,
    })

    assert f.get("parameter.variable") == "q"
    assert f.get("metadata.shortName") is None
    assert f.get("vertical.level") == 600
    assert f.get("metadata.levelist") is None
    assert f.get(("metadata.date", "parameter.variable")) == (None, "q")
    assert f.get(("parameter.variable", "metadata.date")) == ("q", None)
    assert np.allclose(f.values, vals_ori + 1)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()[0]
        assert f_saved.get("parameter.variable") == "q"
        assert f_saved.get("metadata.shortName") == "q"
        assert f_saved.get("vertical.level") == 600
        assert f_saved.get("metadata.levelist") == 600
        assert np.allclose(f_saved.values, vals_ori + 1)

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].set({
        "values": vals_ori + 1,
        "parameter.variable": "q",
        "vertical.level": 600,
    })
    f = f.set({
        "values": vals_ori + 2,
        "parameter.variable": "pt",
        "vertical.level": 800,
    })

    assert f.get("parameter.variable") == "pt"
    assert f.get("metadata.shortName") is None
    assert f.get("vertical.level") == 800
    assert f.get("metadata.levelist") is None
    assert f.get(("metadata.date", "parameter.variable")) == (None, "pt")
    assert f.get(("parameter.variable", "metadata.date")) == ("pt", None)
    assert np.allclose(f.values, vals_ori + 2)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        f = ds_ori[i].set({
            "values": vals_ori + i + 1,
            "parameter.variable": "q",
            "vertical.level": 600,
        })
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.get("parameter.variable") == ["q", "q"]
    assert ds.get("metadata.shortName") == [None, None]
    assert ds.get("vertical.level") == [600, 600]
    assert ds.get("metadata.levelist") == [None, None]
    assert np.allclose(ds[0].values, vals_ori + 1)
    assert np.allclose(ds[1].values, vals_ori + 2)

    # write back to grib
    with temp_file() as tmp:
        ds.to_target("file", tmp)
        ds_saved = from_source("file", tmp).to_fieldlist()
        assert ds_saved.get("parameter.variable") == ["q", "q"]
        assert ds_saved.get("metadata.shortName") == ["q", "q"]
        assert ds_saved.get("vertical.level") == [600, 600]
        assert ds_saved.get("metadata.levelist") == [600, 600]
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
def test_grib_set_default(fl_type):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].set()

    assert f.get("parameter.variable") == "t"
    assert f.get("metadata.shortName") == "t"
    assert f.get("vertical.level") == 500
    assert f.get("metadata.levelist") == 500
    assert f.get("metadata.date", "parameter.variable") == (20070101, "t")
    assert f.get("parameter.variable", "metadata.date") == ("t", 20070101)
    assert np.allclose(f.values, vals_ori)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()[0]
        assert f_saved.get("parameter.variable") == "t"
        assert f_saved.get("metadata.shortName") == "t"
        assert f_saved.get("vertical.level") == 500
        assert f_saved.get("metadata.levelist") == 500
        assert np.allclose(f_saved.values, vals_ori)


@pytest.mark.skip(reason="Not sure if it will ever be implemented")
@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
def test_grib_set_with_metadata_object(fl_type):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    md = ds_ori[0].metadata().override(shortName="q", level=600)

    f = ds_ori[0].set(metadata=md)

    assert f.get("parameter.variable") == "q"
    assert f.get("metadata.shortName") == "q"
    assert f.get("vertical.level") == 600
    assert f.get("metadata.levelist") == 600
    assert f.get("metadata.date", "parameter.variable") == (20070101, "q")
    assert f.get("parameter.variable", "metadata.date") == ("q", 20070101)
    assert np.allclose(f.values, vals_ori)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()[0]
        assert f_saved.get("param") == "q"
        assert f_saved.get("shortName") == "q"
        assert f_saved.get("level") == 600
        assert f_saved.get("levelist") == 600
        assert np.allclose(f_saved.values, vals_ori)

    with pytest.raises(ValueError):
        ds_ori[0].set(metadata=md, param="q")


@pytest.mark.skip(reason="Not sure if it will ever be implemented")
@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
def test_grib_copy_to_field(fl_type):
    from earthkit.data.sources.array_list import ArrayField

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
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()[0]
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
        ds.to_target("file", tmp)
        ds_saved = from_source("file", tmp).to_fieldlist()
        assert ds_saved.get("param") == ["q", "q"]
        assert ds_saved.get("shortName") == ["q", "q"]
        assert ds_saved.get("level") == [600, 600]
        assert ds_saved.get("levelist") == [600, 600]
        assert np.allclose(ds_saved[0].values, vals_ori + 1)
        assert np.allclose(ds_saved[1].values, vals_ori + 2)


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_no_args(fl_type):
    ds, _ = load_grib_data("test4.grib", fl_type)

    f = ds[0]
    r = f.set()
    assert r is f


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_field_sync(fl_type):
    ds, _ = load_grib_data("test4.grib", fl_type)

    f = ds[0]
    f = f.set({
        "parameter.variable": "q",
        "vertical.level": 600,
        "labels.my_shape": (181, 360),
        "labels.my_name": "t_500",
    })

    assert f.get("parameter.variable") == "q"
    assert f.get("metadata.shortName") is None
    assert f.get("vertical.level") == 600
    assert f.get("metadata.levelist") is None
    assert f.get(("metadata.date", "parameter.variable")) == (None, "q")
    assert f.get(("parameter.variable", "metadata.date")) == ("q", None)

    f1 = f.sync()
    assert f1.get("parameter.variable") == "q"
    assert f1.get("metadata.shortName") == "q"
    assert f1.get("vertical.level") == 600
    assert f1.get("metadata.levelist") == 600
    assert f1.get(("metadata.date", "parameter.variable")) == (20070101, "q")
    assert f1.get(("parameter.variable", "metadata.date")) == ("q", 20070101)
    assert f1.get("labels.my_shape") == (181, 360)
    assert f1.get("labels.my_name") == "t_500"
