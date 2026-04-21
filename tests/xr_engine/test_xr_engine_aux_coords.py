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

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_remote_test_data_file


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_aux_coords_simple(lazy_load, allow_holes):
    """aux_coords with a single metadata key mapped to a single dimension."""
    fl = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl_small.grib")).to_fieldlist()
    ds = fl.to_xarray(
        aux_coords={"centre": ("metadata.centre", "forecast_reference_time")},
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    assert "centre" in ds.coords
    assert "centre" not in ds.sizes
    assert ds["centre"].dims == ("forecast_reference_time",)
    assert (ds["centre"] == "ecmf").all()


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_aux_coords_multi_dim(lazy_load, allow_holes):
    """aux_coords mapped to multiple dimensions."""
    fl = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl_small.grib")).to_fieldlist()
    ds = fl.to_xarray(
        aux_coords={"centre": ("metadata.centre", ("forecast_reference_time", "step"))},
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    assert "centre" in ds.coords
    assert "centre" not in ds.sizes
    assert ds["centre"].dims == ("forecast_reference_time", "step")
    assert (ds["centre"] == "ecmf").all()


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_aux_coords_with_remapping(lazy_load, allow_holes):
    """aux_coords using a remapped key."""
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl_small.grib")).to_fieldlist()
    ds = ds0.to_xarray(
        remapping={"centre_class": "{metadata.centre}_{metadata.class}"},
        aux_coords={"centre_class": ("centre_class", ("forecast_reference_time", "step"))},
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    assert "centre_class" in ds.coords
    assert "centre_class" not in ds.sizes
    assert ds["centre_class"].dims == ("forecast_reference_time", "step")
    assert (ds["centre_class"] == "ecmf_od").all()


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_aux_coords_multiple_coords(lazy_load, allow_holes):
    """Multiple aux_coords specified at once."""
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl_small.grib")).to_fieldlist()
    ds = ds0.to_xarray(
        profile="mars",
        aux_coords={
            "centre": ("metadata.centre", "forecast_reference_time"),
            "class_coord": ("metadata.class", "forecast_reference_time"),
        },
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    assert "centre" in ds.coords
    assert "class_coord" in ds.coords
    assert "centre" not in ds.sizes
    assert "class_coord" not in ds.sizes
    assert ds["centre"].dims == ("forecast_reference_time",)
    assert ds["class_coord"].dims == ("forecast_reference_time",)
    assert (ds["centre"] == "ecmf").all()
    assert (ds["class_coord"] == "od").all()


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
def test_xr_engine_aux_coords_unknown_dim(allow_holes):
    """aux_coords referencing a non-existent dimension should raise."""
    fl = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl_small.grib")).to_fieldlist()
    with pytest.raises(AssertionError, match="unknown dimension"):
        fl.to_xarray(
            aux_coords={"centre": ("metadata.centre", "nonexistent_dim")},
            allow_holes=allow_holes,
        )


def test_xr_engine_aux_coords_invalid_spec():
    """aux_coords with invalid tuple specification should raise ValueError."""
    from earthkit.data.xr_engine.profile import AuxCoords

    with pytest.raises(ValueError, match="invalid specification"):
        AuxCoords({"bad": "not_a_tuple"})


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
def test_xr_engine_aux_coords_empty(allow_holes):
    """Empty aux_coords should produce no extra coordinates."""
    fl = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl_small.grib")).to_fieldlist()
    ds_no_aux = fl.to_xarray(aux_coords={}, allow_holes=allow_holes)
    ds_none = fl.to_xarray(allow_holes=allow_holes)

    assert set(ds_no_aux.coords) == set(ds_none.coords)


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_aux_coords_drop_dim_as_aux(lazy_load, allow_holes):
    """Drop a dimension and re-add it as an auxiliary coordinate."""
    fl = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl_small.grib")).to_fieldlist()

    ds = fl.to_xarray(
        time_dims="valid_time",
        aux_coords={"step": ("time.step", ("valid_time",))},
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    # step should be a coordinate but not a dimension
    assert "step" in ds.coords
    assert "step" not in ds.sizes
    assert "valid_time" in ds.coords["step"].dims
    assert (ds.coords["step"] == np.array([0, 6] * 4, dtype="m8[h]")).all()


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_aux_coords_with_mono_variable(lazy_load, allow_holes):
    """aux_coords combined with mono_variable mode."""
    fl = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl_small.grib")).to_fieldlist()
    ds = fl.to_xarray(
        fixed_dims=["parameter.variable", "time.forecast_reference_time", "time.step", "vertical.level"],
        mono_variable=True,
        aux_coords={"metadata_paramId": ("metadata.paramId", "parameter.variable")},
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )
    assert "metadata_paramId" in ds.coords
    assert "metadata_paramId" not in ds.sizes
    assert (ds["metadata_paramId"] == [157, 130]).all()


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_aux_coords_conflicting_values_strict(lazy_load, allow_holes):
    """With strict=True, conflicting aux_coord values for same dim coords should raise."""
    fl = from_source("url", earthkit_remote_test_data_file("xr_engine/level/mixed_pl_ml_small.grib")).to_fieldlist()

    with pytest.raises(AssertionError, match="Conflicting values"):
        _ = fl.to_xarray(
            strict=True,
            level_dim_mode="level_and_type",
            aux_coords={"levtype": ("metadata.levtype", "forecast_reference_time")},
            lazy_load=lazy_load,
            allow_holes=allow_holes,
        )

    ds = fl.to_xarray(
        strict=True,
        level_dim_mode="level_and_type",
        aux_coords={"levtype": ("metadata.levtype", "level_and_type")},
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )
    assert "levtype" in ds.coords
    assert "levtype" not in ds.sizes
    assert (ds["levtype"] == ["ml", "pl", "pl", "ml"]).all()
