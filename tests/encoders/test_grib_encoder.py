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

import numpy as np
import pytest

from earthkit.data import create_encoder, from_source
from earthkit.data.utils.testing import earthkit_examples_file

_LABELS = {"my_label": "my_val"}
_LABELS_SET_ARGS = {"labels.my_label": "my_val"}


@pytest.mark.parametrize("_args,_kwargs", [(("<f>",), {}), ((), {"data": "<f>"}), ((), {"template": "<f>"})])
def test_grib_encoder_field_1(_args, _kwargs):
    f = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()[0]

    _args = tuple(f if v == "<f>" else v for v in _args)
    _kwargs = {k: (f if v == "<f>" else v) for k, v in _kwargs.items()}

    encoder = create_encoder("grib")
    r = encoder.encode(*_args, **_kwargs)

    assert r.to_bytes() == f.message()

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() == f_r.message()
    assert np.allclose(f.values, f_r.values)
    assert f.get("parameter.variable") == f_r.get("parameter.variable")


@pytest.mark.parametrize("init_encoder", [None, ["template"]])
@pytest.mark.parametrize("template_arg", ["field", "field_labels", "message", "handle", "raw_handle"])
def test_grib_encoder_field_template_only(init_encoder, template_arg):
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    template = fl[1]

    if template_arg == "message":
        template_arg_d = template.message()
    elif template_arg == "field":
        template_arg_d = template
    elif template_arg == "field_labels":
        template = template.set(_LABELS_SET_ARGS)
        template_arg_d = template
    elif template_arg == "handle":
        template_arg_d = template._get_grib().handle
    elif template_arg == "raw_handle":
        # this is the clone of the raw handle
        template_arg_d = template._get_grib().handle._raw_handle()
    else:
        raise ValueError(f"Invalid template_arg: {template_arg}")

    assert template.get("parameter.variable") == "msl"

    encoder_kwargs = {}
    encode_kwargs = {"template": template_arg_d}
    if init_encoder is not None:
        for key in init_encoder:
            if key in encode_kwargs:
                encoder_kwargs[key] = encode_kwargs.pop(key)

    encoder = create_encoder("grib", **encoder_kwargs)
    r = encoder.encode(**encode_kwargs)

    assert r.to_bytes() == template.message()

    f_r = r.to_field()
    assert f_r.message() is not None
    assert template.message() == f_r.message()
    assert np.allclose(template.values, f_r.values)
    assert f_r.get("parameter.variable") == "msl"
    if template_arg == "field_labels":
        assert f_r.labels.to_dict() == _LABELS


@pytest.mark.parametrize("init_encoder", [None, ["template"]])
@pytest.mark.parametrize("template_arg", ["field", "field_labels", "message", "handle", "raw_handle"])
def test_grib_encoder_field_data_and_template(init_encoder, template_arg):
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]
    template = fl[1]

    if template_arg == "message":
        template_arg_d = template.message()
    elif template_arg == "field":
        template_arg_d = template
    elif template_arg == "field_labels":
        template = template.set(_LABELS_SET_ARGS)
        template_arg_d = template
    elif template_arg == "handle":
        template_arg_d = template._get_grib().handle
    elif template_arg == "raw_handle":
        template_arg_d = template._get_grib().handle._raw_handle()
    else:
        raise ValueError(f"Invalid template_arg: {template_arg}")

    assert f.get("parameter.variable") == "2t"
    assert template.get("parameter.variable") == "msl"

    encoder_kwargs = {}
    encode_kwargs = {"template": template_arg_d}
    if init_encoder is not None:
        for key in init_encoder:
            if key in encode_kwargs:
                encoder_kwargs[key] = encode_kwargs.pop(key)

    encoder = create_encoder("grib", **encoder_kwargs)
    r = encoder.encode(data=f, **encode_kwargs)

    assert r.to_bytes() != f.message()

    f_r = r.to_field()
    assert f is not f_r
    assert f_r.message() is not None
    assert f.message() != f_r.message()
    assert f_r.message() == r.to_bytes()
    assert np.allclose(f.values, f_r.values)
    assert f.get("parameter.variable") == "2t"
    assert f_r.get("parameter.variable") == "msl"
    if template_arg == "field_labels":
        assert f_r.labels.to_dict() == _LABELS


@pytest.mark.parametrize("init_encoder", [None, ["template"]])
@pytest.mark.parametrize("template_arg", ["field", "field_labels", "message", "handle", "raw_handle"])
def test_grib_encoder_field_values_and_template(init_encoder, template_arg):
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]
    vals = f.values + 1.0
    template = fl[1]

    if template_arg == "message":
        template_arg_d = template.message()
    elif template_arg == "field":
        template_arg_d = template
    elif template_arg == "field_labels":
        template = template.set(_LABELS_SET_ARGS)
        template_arg_d = template
    elif template_arg == "handle":
        template_arg_d = template._get_grib().handle
    elif template_arg == "raw_handle":
        template_arg_d = template._get_grib().handle._raw_handle()
    else:
        raise ValueError(f"Invalid template_arg: {template_arg}")

    assert f.get("parameter.variable") == "2t"
    assert template.get("parameter.variable") == "msl"

    encoder_kwargs = {}
    encode_kwargs = {"template": template_arg_d}
    if init_encoder is not None:
        for key in init_encoder:
            if key in encode_kwargs:
                encoder_kwargs[key] = encode_kwargs.pop(key)

    encoder = create_encoder("grib", **encoder_kwargs)
    r = encoder.encode(values=vals, **encode_kwargs)

    assert r.to_bytes() != f.message()

    f_r = r.to_field()
    assert f is not f_r
    assert f_r.message() is not None
    assert f.message() != f_r.message()
    assert f_r.message() == r.to_bytes()
    assert np.allclose(f.values + 1.0, f_r.values)
    assert f.get("parameter.variable") == "2t"
    assert f_r.get("parameter.variable") == "msl"
    if template_arg == "field_labels":
        assert f_r.labels.to_dict() == _LABELS


def test_grib_encoder_field_data_and_values_and_template():
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]
    vals = f.values + 1.0
    template = fl[1]

    encoder = create_encoder("grib")
    with pytest.raises(ValueError):
        encoder.encode(data=f, values=vals, template=template)


@pytest.mark.parametrize("init_encoder", [None, ["template", "metadata"], ["template"], ["metadata"]])
def test_grib_encoder_field_grib_metadata_1(init_encoder):
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]

    encoder_kwargs = {}
    encode_kwargs = {"template": f, "metadata": {"date": 19980502}}
    if init_encoder is not None:
        for key in init_encoder:
            if key in encode_kwargs:
                encoder_kwargs[key] = encode_kwargs.pop(key)

    encoder = create_encoder("grib", **encoder_kwargs)
    r = encoder.encode(data=f, **encode_kwargs)

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() != f_r.message()
    assert np.allclose(f.values, f_r.values)
    assert f.get("time.base_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f_r.get("time.base_datetime") == datetime.datetime(1998, 5, 2, 12)


def test_grib_encoder_field_grib_metadata_2():
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]

    encoder = create_encoder("grib", metadata={"time": 0})
    r = encoder.encode(data=f, template=f, metadata={"date": 19980502})

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() != f_r.message()
    assert np.allclose(f.values, f_r.values)
    assert f.get("time.base_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f_r.get("time.base_datetime") == datetime.datetime(1998, 5, 2, 0)


def test_grib_encoder_field_grib_metadata_3():
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]
    vals = f.values + 1.0

    encoder = create_encoder("grib", metadata={"time": 0})
    r = encoder.encode(values=vals, template=f, metadata={"date": 19980502})

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() != f_r.message()
    assert np.allclose(f.values + 1.0, f_r.values)

    assert f.get("time.base_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.valid_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.step") == datetime.timedelta(hours=0)
    assert f.get("metadata.dataDate") == 20200513
    assert f.get("metadata.dataTime") == 1200
    assert f.get("metadata.step") == 0
    assert f.get("metadata.validityDate") == 20200513
    assert f.get("metadata.validityTime") == 1200

    assert f_r.get("time.base_datetime") == datetime.datetime(1998, 5, 2, 0)
    assert f_r.get("time.valid_datetime") == datetime.datetime(1998, 5, 2, 0)
    assert f_r.get("time.step") == datetime.timedelta(hours=0)
    assert f_r.get("metadata.dataDate") == 19980502
    assert f_r.get("metadata.dataTime") == 0
    assert f_r.get("metadata.step") == 0
    assert f_r.get("metadata.validityDate") == 19980502
    assert f_r.get("metadata.validityTime") == 0


@pytest.mark.parametrize("init_encoder", [None, ["template", "metadata"], ["template"], ["metadata"]])
@pytest.mark.parametrize(
    "new_base_datetime_metadata", [19980502, datetime.datetime(1998, 5, 2, 0, 0), "1998-05-02T00:00:00"]
)
def test_grib_encoder_field_hl_metadata_1(init_encoder, new_base_datetime_metadata):
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]

    encoder_kwargs = {}
    encode_kwargs = {"template": f, "metadata": {"time.base_datetime": new_base_datetime_metadata}}
    if init_encoder is not None:
        for key in init_encoder:
            if key in encode_kwargs:
                encoder_kwargs[key] = encode_kwargs.pop(key)

    encoder = create_encoder("grib", **encoder_kwargs)
    r = encoder.encode(data=f, **encode_kwargs)

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() != f_r.message()
    assert np.allclose(f.values, f_r.values)

    assert f.get("time.base_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.valid_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.step") == datetime.timedelta(hours=0)
    assert f.get("metadata.dataDate") == 20200513
    assert f.get("metadata.dataTime") == 1200
    assert f.get("metadata.step") == 0
    assert f.get("metadata.validityDate") == 20200513
    assert f.get("metadata.validityTime") == 1200

    assert f_r.get("time.base_datetime") == datetime.datetime(1998, 5, 2, 0)
    assert f_r.get("time.valid_datetime") == datetime.datetime(1998, 5, 2, 0)
    assert f_r.get("time.step") == datetime.timedelta(hours=0)
    assert f_r.get("metadata.dataDate") == 19980502
    assert f_r.get("metadata.dataTime") == 0
    assert f_r.get("metadata.step") == 0
    assert f_r.get("metadata.validityDate") == 19980502
    assert f_r.get("metadata.validityTime") == 0


def test_grib_encoder_field_hl_metadata_2():
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]

    encoder = create_encoder("grib", metadata={"time.step": 6})
    r = encoder.encode(data=f, template=f, metadata={"time.base_datetime": datetime.datetime(1998, 5, 2, 0, 0)})

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() != f_r.message()
    assert np.allclose(f.values, f_r.values)

    assert f.get("time.base_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.valid_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.step") == datetime.timedelta(hours=0)
    assert f.get("metadata.dataDate") == 20200513
    assert f.get("metadata.dataTime") == 1200
    assert f.get("metadata.step") == 0
    assert f.get("metadata.validityDate") == 20200513
    assert f.get("metadata.validityTime") == 1200

    assert f_r.get("time.base_datetime") == datetime.datetime(1998, 5, 2, 0)
    assert f_r.get("time.valid_datetime") == datetime.datetime(1998, 5, 2, 6)
    assert f_r.get("time.step") == datetime.timedelta(hours=6)
    assert f_r.get("metadata.dataDate") == 19980502
    assert f_r.get("metadata.dataTime") == 0
    assert f_r.get("metadata.step") == 6
    assert f_r.get("metadata.validityDate") == 19980502
    assert f_r.get("metadata.validityTime") == 600


def test_grib_encoder_field_hl_metadata_3():
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]
    vals = f.values + 1.0

    encoder = create_encoder("grib", metadata={"time.step": 6})
    r = encoder.encode(values=vals, template=f, metadata={"time.base_datetime": datetime.datetime(1998, 5, 2, 0, 0)})

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() != f_r.message()
    assert np.allclose(f.values + 1.0, f_r.values)

    assert f.get("time.base_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.valid_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.step") == datetime.timedelta(hours=0)
    assert f.get("metadata.dataDate") == 20200513
    assert f.get("metadata.dataTime") == 1200
    assert f.get("metadata.step") == 0
    assert f.get("metadata.validityDate") == 20200513
    assert f.get("metadata.validityTime") == 1200

    assert f_r.get("time.base_datetime") == datetime.datetime(1998, 5, 2, 0)
    assert f_r.get("time.valid_datetime") == datetime.datetime(1998, 5, 2, 6)
    assert f_r.get("time.step") == datetime.timedelta(hours=6)
    assert f_r.get("metadata.dataDate") == 19980502
    assert f_r.get("metadata.dataTime") == 0
    assert f_r.get("metadata.step") == 6
    assert f_r.get("metadata.validityDate") == 19980502
    assert f_r.get("metadata.validityTime") == 600


def test_grib_encoder_field_mixed_metadata():
    fl = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

    f = fl[0]
    vals = f.values + 1.0

    encoder = create_encoder("grib", metadata={"metadata.step": 5, "metadata.time": 600})
    r = encoder.encode(values=vals, template=f, metadata={"time.base_datetime": datetime.datetime(1998, 5, 2, 0, 0)})

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() != f_r.message()
    assert np.allclose(f.values + 1.0, f_r.values)

    assert f.get("time.base_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.valid_datetime") == datetime.datetime(2020, 5, 13, 12, 0)
    assert f.get("time.step") == datetime.timedelta(hours=0)
    assert f.get("metadata.dataDate") == 20200513
    assert f.get("metadata.dataTime") == 1200
    assert f.get("metadata.step") == 0
    assert f.get("metadata.validityDate") == 20200513
    assert f.get("metadata.validityTime") == 1200

    assert f_r.get("time.base_datetime") == datetime.datetime(1998, 5, 2, 6)
    assert f_r.get("time.valid_datetime") == datetime.datetime(1998, 5, 2, 11)
    assert f_r.get("time.step") == datetime.timedelta(hours=5)
    assert f_r.get("metadata.dataDate") == 19980502
    assert f_r.get("metadata.dataTime") == 600
    assert f_r.get("metadata.step") == 5
    assert f_r.get("metadata.validityDate") == 19980502
    assert f_r.get("metadata.validityTime") == 1100


@pytest.mark.parametrize("_args,_kwargs", [(("<f>",), {}), ((), {"data": "<f>"}), ((), {"template": "<f>"})])
def test_grib_encoder_field_labels_1(_args, _kwargs):
    f = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()[0]

    f = f.set({"labels.my_label": "val"})

    _args = tuple(f if v == "<f>" else v for v in _args)
    _kwargs = {k: (f if v == "<f>" else v) for k, v in _kwargs.items()}

    encoder = create_encoder("grib")
    r = encoder.encode(*_args, **_kwargs)

    assert r.to_bytes() == f.message()

    f_r = r.to_field()
    assert f is not f_r
    assert f.message() == f_r.message()
    assert np.allclose(f.values, f_r.values)
    assert f.get("parameter.variable") == f_r.get("parameter.variable")
    assert f.get("labels.my_label") == "val"
