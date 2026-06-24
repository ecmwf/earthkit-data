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

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize(
    "_kwargs,ref1,grib_ref,ref2",
    [
        (
            {
                "vertical.level": 320,
                "vertical.level_type": "potential_temperature",
            },
            {
                "vertical.level": 320,
                "vertical.level_type": "potential_temperature",
                "vertical.units": "K",
                "vertical.abbreviation": "pt",
                "metadata.levelist": None,
                "metadata.level": None,
                "metadata.levtype": None,
                "metadata.typeOfLevel": None,
            },
            {
                "levelist": 500,
                "level": 500,
                "levtype": "pl",
                "typeOfLevel": "isobaricInhPa",
            },
            {
                "vertical.level": 320,
                "vertical.level_type": "potential_temperature",
                "metadata.levelist": 320,
                "metadata.level": 320,
                "metadata.levtype": "pt",
                "metadata.typeOfLevel": "theta",
            },
        ),
        # (
        #     {
        #         "vertical.level": 300,
        #         "vertical.level_type": "temperature",
        #     },
        #     {
        #         "vertical.level": 300,
        #         "vertical.level_type": "temperature",
        #         "vertical.units": "K",
        #         "vertical.abbreviation": "isothermal",
        #         "metadata.levelist": 500,
        #         "metadata.level": 500,
        #         "metadata.levtype": "pl",
        #         "metadata.typeOfLevel": "isobaricInhPa",
        #     },
        #     {
        #         "vertical.level": 300,
        #         "vertical.level_type": "temperature",
        #         "metadata.levelist": 300,
        #         "metadata.level": 300,
        #         "metadata.levtype": "isothermal",
        #         "metadata.typeOfLevel": "isothermal",
        #     },
        # ),
    ],
)
def test_grib_set_vertical(fl_type, _kwargs, ref1, grib_ref, ref2):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)

    for k, v in ref1.items():
        assert f.get(k) == v

    # the original field is unchanged
    assert ds_ori[0].get("vertical.level") == 500
    assert ds_ori[0].get("vertical.level_type") == "pressure"

    # the field still stores the original GRIB metadata as private metadata,
    # which is hidden but used when writing back to GRIB
    grib_md = f._get_grib()
    for k, v in grib_ref.items():
        assert grib_md.get(k) == v

    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        for k, v in ref2.items():
            assert f_saved[0].get(k) == v, f"key {k} expected {v} got {f_saved[0].get(k)}"


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_vertical_hybrid_1(fl_type):
    ds_ori, _ = load_grib_data("ml_data.grib", fl_type, folder="data")
    f_ori = ds_ori[0]

    f = f_ori.set({"vertical.level": 2})
    assert f.vertical.level() == 2
    assert f.vertical.level_type() == "hybrid"
    assert f.vertical.number_of_levels() == 137
    A, B = f.vertical.coefficients()
    assert len(A) == 138
    assert len(B) == 138

    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()[0]
        assert f_saved.vertical.level() == 2
        assert f_saved.vertical.level_type() == "hybrid"
        assert f_saved.vertical.number_of_levels() == 137
        A1, B1 = f_saved.vertical.coefficients()
        assert np.allclose(A, A1)
        assert np.allclose(B, B1)


@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize("coeff_mode", ["object", "tuple"])
@pytest.mark.parametrize(
    "input_file, _kwargs",
    [
        (("ml_data.grib", "data"), {}),
        (("test4.grib", "example"), {"vertical.level_type": "hybrid", "vertical.level": 1}),
    ],
)
def test_grib_set_vertical_hybrid_coefficients_1(fl_type, coeff_mode, input_file, _kwargs):
    file_name, folder = input_file
    ds_ori, _ = load_grib_data(file_name, fl_type, folder=folder)
    f_ori = ds_ori[0]

    A = np.array([0.0, 2.000365, 4.00073, 6.001095] + [0.0] * 88)
    B = np.array([0.0, 0.0, 0.0, 0.0] + [1.0] * 88)

    level_num = len(A) - 1

    if coeff_mode == "object":
        from earthkit.data.field.component.level_parameters import HybridLevelParameters

        coeff = HybridLevelParameters(A=A, B=B)

    elif coeff_mode == "tuple":
        coeff = (A, B)
    else:
        raise ValueError(f"Invalid coeff_mode '{coeff_mode}'")

    f = f_ori.set({"vertical.coefficients": coeff}, _kwargs)

    ref1 = {
        "vertical.level": 1,
        "vertical.level_type": "hybrid",
        "vertical.number_of_levels": level_num,
        "metadata.levelist": None,
        "metadata.level": None,
        "metadata.levtype": None,
        "metadata.typeOfLevel": None,
    }

    for k, v in ref1.items():
        assert f.get(k) == v

    A1, B1 = f.vertical.coefficients()
    assert np.allclose(A1, A)
    assert np.allclose(B1, B)

    f = f.sync()

    ref2 = {
        "vertical.level": 1,
        "vertical.level_type": "hybrid",
        "vertical.number_of_levels": level_num,
        "metadata.levelist": 1,
        "metadata.level": 1,
        "metadata.levtype": "ml",
        "metadata.typeOfLevel": "hybrid",
    }

    for k, v in ref2.items():
        assert f.get(k) == v

    A1, B1 = f.vertical.coefficients()
    assert np.allclose(A1, A)
    assert np.allclose(B1, B)

    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp).to_fieldlist()
        assert len(f_saved) == 1
        for k, v in ref2.items():
            assert f_saved[0].get(k) == v, f"key {k} expected {v} got {f_saved[0].get(k)}"

        A2, B2 = f_saved[0].vertical.coefficients()
        assert np.allclose(A, A2)
        assert np.allclose(B, B2)


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_set_vertical_hybrid_bad(fl_type):
    ds_ori, _ = load_grib_data("ml_data.grib", fl_type, folder="data")
    f_ori = ds_ori[0]

    from earthkit.data.field.component.level_parameters import HybridLevelParameters

    A = np.array([0.0, 2.000365, 4.00073, 6.001095] + [0.0] * 88)
    B = np.array([0.0, 0.0, 0.0, 0.0] + [1.0] * 88)

    level_parameters = HybridLevelParameters(A=A, B=B)

    with pytest.raises(ValueError):
        f_ori.set({"vertical.level_type": "pressure", "vertical.coefficients": (A, B)})

    with pytest.raises(ValueError):
        f_ori.set({"vertical.level_type": "pressure", "vertical.coefficients": level_parameters})
