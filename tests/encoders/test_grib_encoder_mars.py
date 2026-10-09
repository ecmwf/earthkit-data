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

from earthkit.data import create_encoder

EPSILON = 1e-4

MARS_TO_GRIB_KEYS = {
    "origin": None,
    "type": "mars.type",
    "class": "mars.class",
    "stream": "mars.stream",
    "expver": "mars.expver",
    "date": "mars.date",
    "time": "mars.time",
    "step": "mars.step",
    "param": "mars.param",
    "levtype": "levtype",
    "packing": None,
    "bitsPerValue": "bitsPerValue",
    "accuracy": "bitsPerValue",
}


@pytest.mark.parametrize(
    "grid,shape,grid_ref",
    [
        ({"grid": "1/1"}, (181, 360), {"gridType": "regular_ll"}),
        ({"grid": "O96"}, (40320,), {"gridType": "reduced_gg", "N": 96, "isOctahedral": 1}),
        ({"grid": "N96"}, (50662,), {"gridType": "reduced_gg", "N": 96, "isOctahedral": 0}),
    ],
)
def test_grib_encoder_mars_sfc(grid, shape, grid_ref):
    data = np.random.random(shape)

    metadata = {
        "origin": "ecmf",
        "type": "fc",
        "class": "od",
        "stream": "oper",
        "expver": "0001",
        "date": 20010101,
        "time": 00,
        "step": 6,
        "param": 167,
        "levtype": "sfc",
        "packing": "ccsds",
        **grid,
    }

    encoder = create_encoder("grib")
    r = encoder.encode(
        mars_metadata=metadata,
        values=data,
    )
    f_r = r.to_field()

    assert f_r.get("metadata.shortName") == "2t"
    assert f_r.get("metadata.date") == 20010101
    assert f_r.get("metadata.shortName") == "2t"
    assert f_r.get("metadata.levtype") == "sfc"
    assert f_r.get("metadata.edition") == 2
    # assert f_r.get("metadata.generatingProcessIdentifier") == 255
    assert f_r.shape == shape
    for k, v in grid_ref.items():
        assert f_r.get(f"metadata.{k}") == v, f"{k}: {f_r.get(f'metadata.{k}')}!={v}"

    for k, v in metadata.items():
        k = MARS_TO_GRIB_KEYS.get(k)
        if k is not None:
            assert f_r.get(f"metadata.{k}") == v, f"{k}: {f_r.get(f'metadata.{k}')}!={v}"

    assert f_r.geography.shape() == shape
    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


def test_grib_encoder_mars_pl():
    shape = (40320,)
    data = np.random.random(shape)

    metadata = {
        "origin": "ecmf",
        "type": "fc",
        "class": "od",
        "stream": "oper",
        "expver": "0001",
        "date": 20010101,
        "time": 00,
        "step": 6,
        "param": 130,
        "levtype": "pl",
        "levelist": 850,
        "packing": "ccsds",
        "grid": "o96",
    }

    encoder = create_encoder("grib")
    r = encoder.encode(mars_metadata=metadata, values=data)
    f_r = r.to_field()

    assert f_r.get("metadata.date") == 20010101
    assert f_r.get("metadata.edition") == 2
    # TODO: with the current pymetkit we get 8. Change this once pymetkit is updated.
    # assert f_r.get("metadata.level") == 850
    assert f_r.get("metadata.levtype") == "pl"
    assert f_r.get("metadata.shortName") == "t"
    # assert f_r.get("metadata.generatingProcessIdentifier") == 255
    assert f_r.get("metadata.gridType") == "reduced_gg"
    assert f_r.get("metadata.N") == 96
    assert f_r.get("metadata.isOctahedral") == 1

    for k, v in metadata.items():
        k = MARS_TO_GRIB_KEYS.get(k)
        if k is not None:
            assert f_r.get(f"metadata.{k}") == v, f"{k}: {f_r.get(f'metadata.{k}')}!={v}"

    assert f_r.geography.shape() == shape
    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skip(reason="Currently fails due to pymetkit handling of accuracy")
def test_grib_encoder_mars_accuracy():
    shape = (40320,)
    data = np.random.random(shape)

    metadata = {
        "origin": "ecmf",
        "type": "fc",
        "class": "od",
        "stream": "oper",
        "expver": "0001",
        "date": 20010101,
        "time": 00,
        "step": 6,
        "param": 167,
        "levtype": "sfc",
        "packing": "ccsds",
        "grid": "o96",
        "accuracy": 12,
    }

    encoder = create_encoder("grib")
    r = encoder.encode(mars_metadata=metadata, values=data)
    f_r = r.to_field()

    assert f_r.get("metadata.date") == 20010101
    assert f_r.get("metadata.edition") == 2
    # TODO: with the current pymetkit we get 8. Change this once pymetkit is updated.
    # assert f_r.get("metadata.level") == 850
    assert f_r.get("metadata.levtype") == "sfc"
    assert f_r.get("metadata.bitsPerValue") == 12
    assert f_r.get("metadata.shortName") == "2t"
    # assert f_r.get("metadata.generatingProcessIdentifier") == 255
    assert f_r.get("metadata.gridType") == "reduced_gg"
    assert f_r.get("metadata.N") == 96
    assert f_r.get("metadata.isOctahedral") == 1

    for k, v in metadata.items():
        k = MARS_TO_GRIB_KEYS.get(k)
        if k is not None:
            assert f_r.get(f"metadata.{k}") == v, f"{k}: {f_r.get(f'metadata.{k}')}!={v}"

    assert f_r.geography.shape() == shape
    assert np.allclose(f_r.to_numpy(), data, rtol=EPSILON, atol=EPSILON)


def test_grib_encoder_mars_bits_per_value():
    shape = (40320,)
    data = np.random.random(shape) * 300.0 + 1.0  # mimic temperature range

    mars_metadata = {
        "origin": "ecmf",
        "type": "fc",
        "class": "od",
        "stream": "oper",
        "expver": "0001",
        "date": 20010101,
        "time": 00,
        "step": 6,
        "param": 167,
        "levtype": "sfc",
        "packing": "ccsds",
        "grid": "o96",
    }

    metadata = {"bitsPerValue": 12}

    encoder = create_encoder("grib")
    r = encoder.encode(mars_metadata=mars_metadata, metadata=metadata, values=data)
    f_r = r.to_field()

    assert f_r.get("metadata.date") == 20010101
    assert f_r.get("metadata.edition") == 2
    # TODO: with the current pymetkit we get 8. Change this once pymetkit is updated.
    # assert f_r.get("metadata.level") == 850
    assert f_r.get("metadata.levtype") == "sfc"
    assert f_r.get("metadata.bitsPerValue") == 12
    assert f_r.get("metadata.shortName") == "2t"
    # assert f_r.get("metadata.generatingProcessIdentifier") == 255
    assert f_r.get("metadata.gridType") == "reduced_gg"
    assert f_r.get("metadata.N") == 96
    assert f_r.get("metadata.isOctahedral") == 1

    for k, v in mars_metadata.items():
        k = MARS_TO_GRIB_KEYS.get(k)
        if k is not None:
            assert f_r.get(f"metadata.{k}") == v, f"{k}: {f_r.get(f'metadata.{k}')}!={v}"

    assert f_r.get("metadata.bitsPerValue") == 12

    assert f_r.geography.shape() == shape

    np.testing.assert_allclose(f_r.to_numpy(), data, atol=0.1, verbose=False)
