#!/usr/bin/env python3

# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import pytest

from earthkit.data import create_encoder, from_source
from earthkit.data.utils.testing import earthkit_examples_file

EPSILON = 1e-4


# @pytest.mark.parametrize("fl_type", FL_ARRAYS)
# def test_grib_encoder_raw_when_loaded_from_file_core(fl_type):
#     fs, _ = load_grib_data("test6.grib", fl_type)
#     assert len(fs) == 6

#     encoder = create_encoder("grib")
#     r = encoder.encode(data=fs)
#     f_r = [x.to_field() for x in r]
#     assert len(fs) == len(f_r)


# @pytest.mark.parametrize(
#     "_kwargs,expected_value",
#     [({}, 16), ({"metadata.bitsPerValue": 12}, 12)],
# )
# def test_grib_encoder_raw_bits_per_value_fieldlist(
#     _kwargs,
#     expected_value,
# ):
#     ds = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()

#     assert ds[0].get("metadata.bitsPerValue") == 16

#     encoder = create_encoder("grib")
#     r = encoder.encode(data=ds, **_kwargs)
#     f_r = [x.to_field() for x in r]
#     assert [f.get("metadata.bitsPerValue") for f in f_r] == [expected_value] * len(ds)


# @pytest.mark.parametrize("array", [True, False])
# @pytest.mark.parametrize(
#     "_kwargs,expected_value",
#     [({}, 16), ({"metadata.bitsPerValue": 12}, 12)],
# )
# def test_grib_encoder_raw_bits_per_value_single_field(array, _kwargs, expected_value):
#     ds = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()
#     assert ds[0].get("metadata.bitsPerValue") == 16
#     if array:
#         ds = ds.to_fieldlist()

#     encoder = create_encoder("grib")
#     r = encoder.encode(data=ds[0], **_kwargs)
#     f_r = r.to_field()
#     assert f_r.get("metadata.bitsPerValue") == expected_value


# # TODO: if we use missing_value = np.finfo(np.float32).max the test fails
# @pytest.mark.parametrize("missing_value", [100000.0, np.finfo(np.float32).max - 1])
# def test_grib_encoder_raw_missing_value_1(missing_value):
#     fld = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()[0]

#     values = fld.values
#     values[0] = np.nan
#     assert not np.isnan(values[1])

#     encoder = create_encoder("grib")
#     r = encoder.encode(
#         values=values,
#         template=fld,
#         check_nans=True,
#         missing_value=missing_value,
#     )
#     f_r = r.to_field()
#     assert f_r.get("metadata.bitmapPresent") == 1
#     assert np.isnan(f_r.values[0])
#     assert not np.isnan(values[1])


def test_grib_encoder_raw_latlon():
    data = np.random.random((181, 360))

    encoder = create_encoder("grib")
    r = encoder.encode(
        metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
        values=data,
    )
    f_r = r.to_field()

    assert f_r.get("metadata.shortName") == "2t"
    assert f_r.get("metadata.date") == 20010101
    assert f_r.get("metadata.shortName") == "2t"
    assert f_r.get("metadata.levtype") == "sfc"
    assert f_r.get("metadata.edition") == 2
    assert f_r.get("metadata.generatingProcessIdentifier") == 255

    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


def test_grib_encoder_raw_o96_sfc():
    data = np.random.random((40320,))

    encoder = create_encoder("grib")
    r = encoder.encode(
        metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
        values=data,
    )
    f_r = r.to_field()

    ref = {
        "metadata.date": 20010101,
        "metadata.shortName": "2t",
        "metadata.levtype": "sfc",
        "metadata.edition": 2,
        "metadata.generatingProcessIdentifier": 255,
        "metadata.gridType": "reduced_gg",
        "metadata.N": 96,
        "metadata.isOctahedral": 1,
    }

    for k, v in ref.items():
        assert f_r.get(k) == v, f"{k}: {f_r.get(k)}!={v}"

    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


def test_grib_encoder_raw_o160_sfc():
    data = np.random.random((108160,))

    encoder = create_encoder("grib")
    r = encoder.encode(
        metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
        values=data,
    )
    f_r = r.to_field()

    ref = {
        "metadata.date": 20010101,
        "metadata.shortName": "2t",
        "metadata.levtype": "sfc",
        "metadata.edition": 2,
        "metadata.generatingProcessIdentifier": 255,
        "metadata.gridType": "reduced_gg",
        "metadata.N": 160,
        "metadata.isOctahedral": 1,
    }

    for k, v in ref.items():
        assert f_r.get(k) == v, f"{k}: {f_r.get(k)}!={v}"

    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


def test_grib_encoder_raw_n96_sfc():
    data = np.random.random(50662)

    encoder = create_encoder("grib")
    r = encoder.encode(
        metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
        values=data,
    )
    f_r = r.to_field()

    ref = {
        "metadata.date": 20010101,
        "metadata.shortName": "2t",
        "metadata.levtype": "sfc",
        "metadata.edition": 2,
        "metadata.generatingProcessIdentifier": 255,
        "metadata.gridType": "reduced_gg",
        "metadata.N": 96,
        "metadata.isOctahedral": 0,
    }

    for k, v in ref.items():
        assert f_r.get(k) == v, f"{k}: {f_r.get(k)}!={v}"

    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


def test_grib_encoder_raw_mars_labeling():
    data = np.random.random((40320,))

    encoder = create_encoder("grib")
    r = encoder.encode(
        metadata=dict(
            date=20010101,
            generatingProcessIdentifier=255,
            type="fc",
            expver="test",
            step=24,
            param="msl",
        ),
        values=data,
    )
    f_r = r.to_field()

    assert f_r.get("metadata.date") == 20010101
    assert f_r.get("metadata.edition") == 2
    assert f_r.get("metadata.step") == 24
    assert f_r.get("metadata.step") == 24
    assert f_r.get("metadata.expver") == "test"
    assert f_r.get("metadata.levtype") == "sfc"
    assert f_r.get("metadata.shortName") == "msl"
    assert f_r.get("metadata.type") == "fc"
    assert f_r.get("metadata.generatingProcessIdentifier") == 255
    assert f_r.get("metadata.gridType") == "reduced_gg"
    assert f_r.get("metadata.N") == 96
    assert f_r.get("metadata.isOctahedral") == 1

    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.parametrize("levtype", [{}, {"levtype": "pl"}])
def test_grib_encoder_raw_o96_pl(levtype):
    data = np.random.random((40320,))

    _kwargs = dict(date=20010101, generatingProcessIdentifier=255, param="t", level=850)
    _kwargs.update(levtype)

    encoder = create_encoder("grib")
    r = encoder.encode(metadata=_kwargs, values=data)
    f_r = r.to_field()

    assert f_r.get("metadata.date") == 20010101
    assert f_r.get("metadata.edition") == 2
    assert f_r.get("metadata.level") == 850
    assert f_r.get("metadata.levtype") == "pl"
    assert f_r.get("metadata.shortName") == "t"
    assert f_r.get("metadata.generatingProcessIdentifier") == 255
    assert f_r.get("metadata.gridType") == "reduced_gg"
    assert f_r.get("metadata.N") == 96
    assert f_r.get("metadata.isOctahedral") == 1

    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.parametrize("levtype", [{}, {"levtype": "pl"}])
def test_grib_encoder_raw_tp(levtype):
    data = np.random.random((181, 360))

    encoder = create_encoder("grib")
    r = encoder.encode(
        metadata=dict(date=20010101, generatingProcessIdentifier=255, param="tp", step=48, edition=1),
        values=data,
    )
    f_r = r.to_field()

    assert f_r.get("metadata.date") == 20010101
    assert f_r.get("metadata.shortName") == "tp"
    assert f_r.get("metadata.levtype") == "sfc"
    assert f_r.get("metadata.edition") == 1
    assert f_r.get("metadata.step") == 48
    assert f_r.get("metadata.step") == 48
    assert f_r.get("metadata.generatingProcessIdentifier") == 255
    assert f_r.get("metadata.gridType") == "regular_ll"
    assert f_r.get("metadata.Ni") == 360
    assert f_r.get("metadata.Nj") == 181

    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.parametrize("array", [True, False])
def test_grib_encoder_raw_field_template(array):
    data = np.random.random((7, 12))

    ds = from_source("file", earthkit_examples_file("test6.grib")).to_fieldlist()
    if array:
        ds = ds.to_fieldlist()

    encoder = create_encoder("grib")
    r = encoder.encode(
        metadata=dict(date=20010101, generatingProcessIdentifier=255, param="pt", bitsPerValue=16),
        values=data,
        template=ds[0],
    )
    f_r = r.to_field()

    assert f_r.get("metadata.date") == 20010101
    assert f_r.get("metadata.shortName") == "pt"
    assert f_r.get("metadata.levtype") == "pl"
    assert f_r.get("metadata.edition") == 1
    assert f_r.get("metadata.generatingProcessIdentifier") == 255
    assert f_r.get("metadata.bitsPerValue") == 16

    assert np.allclose(f_r.to_numpy(), data, rtol=1e-2, atol=1e-2)
