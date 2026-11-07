#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Tests for the CF hybrid sigma pressure coordinate read by readers.xarray (netCDF and xarray objects)."""

import logging

import numpy as np
import pytest
import xarray as xr

import earthkit.data.field.cf
from earthkit.data import from_object, from_source
from earthkit.data.field.cf import AtmosphereHybridSigmaPressureCoordinate as CLS
from earthkit.data.field.cf import add_parametric_vertical
from earthkit.data.field.component.vertical import ParametricVertical, Vertical
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file

HYBRID = "atmosphere_hybrid_sigma_pressure_coordinate"
N = 137
LAT = [30.0, 20.0, 10.0]
LON = [0.0, 10.0, 20.0, 30.0]
TIMES = np.array(["2020-01-01T00:00", "2020-01-01T06:00"], dtype="datetime64[ns]")


@pytest.fixture(scope="module")
def l137():
    ds = from_source("file", earthkit_test_data_file("ml_data.grib")).to_fieldlist()
    A, B = ds[0].vertical.coefficients()
    return np.asarray(A), np.asarray(B)


def _data(*shape):
    return np.random.default_rng(0).random(shape)


def _read(ds, mode, tmp_path):
    """Read ``ds`` as a netCDF file ("nc") or as an in-memory dataset ("xr")."""
    if mode == "nc":
        path = str(tmp_path / "data.nc")
        ds.to_netcdf(path)
        return from_source("file", path).to_fieldlist()
    return from_object(ds).to_fieldlist()


def _l137_dataset(l137, variables=("t",)):
    """Dataset with ``t(time, level, latitude, longitude)`` and the CF hybrid coordinate of the full L137 model."""
    ds = xr.Dataset(
        {v: (("time", "level", "latitude", "longitude"), _data(2, N, 3, 4)) for v in variables},
        coords={"time": TIMES, "level": np.arange(1, N + 1), "latitude": LAT, "longitude": LON},
    )
    model = CLS.from_half_levels(*l137)
    return add_parametric_vertical(ds, model, "level", ps_dims={"latitude": 3, "longitude": 4})


def _cmip6_dataset(l137, with_level_number=False, mln_first=False):
    """Strict-CF dataset of the full L137 model, stored surface-first, with ``t`` and a CMIP-style ``ps``."""
    A, B = l137
    m = CLS.from_half_levels(A, B)
    p0 = 100000.0

    ap, b = m.ap[::-1], m.b[::-1]
    ap_bnds, b_bnds = m.ap_bnds[::-1], m.b_bnds[::-1]  # (upper, lower)
    lev = ap / p0 + b
    lev_bnds = ap_bnds / p0 + b_bnds

    lev_attrs = {
        "standard_name": HYBRID,
        "units": "1",
        "axis": "Z",
        "positive": "down",
        "bounds": "lev_bnds",
        "formula_terms": "ap: ap b: b ps: ps",
    }
    coords = {}
    mln = ("lev", np.arange(N, 0, -1), {"standard_name": "model_level_number"})
    if with_level_number and mln_first:
        coords["mln"] = mln
    coords["lev"] = ("lev", lev, lev_attrs)
    if with_level_number and not mln_first:
        coords["mln"] = mln
    coords["time"] = TIMES
    coords["lat"] = ("lat", LAT, {"standard_name": "latitude", "units": "degrees_north"})
    coords["lon"] = ("lon", LON, {"standard_name": "longitude", "units": "degrees_east"})

    return xr.Dataset(
        data_vars={
            "t": (("time", "lev", "lat", "lon"), _data(2, N, 3, 4), {"units": "K"}),
            "ps": (
                ("time", "lat", "lon"),
                _data(2, 3, 4) + 1e5,
                {"units": "Pa", "standard_name": "surface_air_pressure"},
            ),
            "ap": ("lev", ap, {"units": "Pa"}),
            "b": ("lev", b),
            "ap_bnds": (("lev", "bnds"), ap_bnds, {"units": "Pa"}),
            "b_bnds": (("lev", "bnds"), b_bnds),
            "lev_bnds": (("lev", "bnds"), lev_bnds, {"formula_terms": "ap: ap_bnds b: b_bnds ps: ps"}),
        },
        coords=coords,
    )


def _levels(fl, var=None):
    if var is not None:
        fl = fl.sel({"parameter.variable": var})
    return [f.vertical.level() for f in fl]


def _check_parametric(fl, l137, levels, var="t"):
    A, B = l137
    fl = fl.sel({"parameter.variable": var})
    assert len(fl) > 0
    assert sorted(set(_levels(fl))) == sorted(levels)
    for f in fl:
        v = f.vertical
        assert isinstance(v, ParametricVertical)
        assert v.level_type() == "hybrid"
        assert v.number_of_levels() == N
        cA, cB = v.coefficients()
        np.testing.assert_array_equal(cA, A)
        np.testing.assert_array_equal(cB, B)


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_full_l137(l137, mode, tmp_path):
    fl = _read(_l137_dataset(l137), mode, tmp_path)

    assert len(fl) == 2 * N
    _check_parametric(fl, l137, range(1, N + 1))

    # selection on level and iteration keep the coefficients
    for sel in ({"vertical.level": 5}, {"vertical.level": [1, 137]}):
        r = fl.sel(sel)
        assert len(r) == 2 * len(np.atleast_1d(list(sel.values())[0]))
        _check_parametric(r, l137, np.atleast_1d(list(sel.values())[0]))

    r = fl.sel({"vertical.level": 10, "time.valid_datetime": "2020-01-01T06:00"})
    assert len(r) == 1
    _check_parametric(r, l137, [10])

    for f in fl[::17]:
        assert isinstance(f.vertical, ParametricVertical)
    assert all(isinstance(f.vertical, ParametricVertical) for f in fl)

    # the placeholder surface pressure is a coordinate, not a field
    assert fl.unique("parameter.variable") == {"parameter.variable": ("t",)}


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_xr_engine_level_subset(mode, tmp_path, caplog):
    ml = from_source("file", earthkit_test_data_file("ml_data.grib")).to_fieldlist()
    ref_levels = ml.sel({"parameter.variable": "t"}).unique("vertical.level")["vertical.level"]
    assert ref_levels[0] == 1 and ref_levels[-1] == N and len(ref_levels) == 35

    ds = ml.to_xarray(add_earthkit_attrs=False)

    with caplog.at_level(logging.DEBUG):
        fl = _read(ds, mode, tmp_path)
        fields = list(fl)

    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert fl.unique("parameter.variable") == {"parameter.variable": ("lnsp", "t")}

    t = [f for f in fields if f.get("parameter.variable") == "t"]
    assert len(t) == 35
    assert tuple(f.vertical.level() for f in t) == tuple(ref_levels)
    for f in t:
        assert f.vertical.level_type() == "hybrid"
        assert type(f.vertical) is Vertical
        assert f.vertical.coefficients() is None


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize("with_level_number", [False, True])
def test_netcdf_hybrid_cmip6(l137, mode, with_level_number, tmp_path):
    ds = _cmip6_dataset(l137, with_level_number=with_level_number)
    assert np.all(np.diff(ds["lev"].values) < 0)  # surface first

    fl = _read(ds, mode, tmp_path)
    t = fl.sel({"parameter.variable": "t"})

    # model order: 1 = top. The dataset is stored surface-first
    assert len(t) == 2 * N
    assert list(dict.fromkeys(_levels(t))) == list(range(N, 0, -1))
    assert all(isinstance(x, int) for x in _levels(t))
    _check_parametric(fl, l137, range(1, N + 1))

    # the level number is that of the model level of the data: array index i is level N - i
    for level in (1, 60, N):
        f = t.sel({"vertical.level": level, "time.valid_datetime": "2020-01-01T00:00"})
        assert len(f) == 1
        np.testing.assert_allclose(f[0].to_numpy(), ds["t"].values[0, N - level])

    # the CMIP-style ps data variable is a field
    ps = fl.sel({"parameter.variable": "ps"})
    assert len(ps) == 2
    assert ps[0].vertical.level_type() == "unknown"
    assert type(ps[0].vertical) is Vertical


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_cmip6_level_numbers_subset(l137, mode, tmp_path):
    # a subset of the model with model_level_number: the levels come from it, no coefficients
    model = CLS.from_half_levels(*l137, levels=list(range(10, 21)))
    ds = model.encode(coord_values="dimensionless", ps_dims=None)
    ds = ds.assign_coords(latitude=LAT, longitude=LON)
    ds["t"] = (("level", "latitude", "longitude"), _data(11, 3, 4))

    fl = _read(ds, mode, tmp_path)
    assert len(fl) == 11
    assert [f.vertical.level() for f in fl] == list(range(10, 21))
    for f in fl:
        assert f.vertical.level_type() == "hybrid"
        assert type(f.vertical) is Vertical
        assert f.vertical.coefficients() is None


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_malformed_formula_terms(l137, mode, tmp_path, caplog):
    ds = _cmip6_dataset(l137)
    ds["lev"].attrs["formula_terms"] = "ap: missing b: b ps: ps"
    lev = ds["lev"].values

    with caplog.at_level(logging.WARNING):
        fl = _read(ds, mode, tmp_path)
        fields = list(fl.sel({"parameter.variable": "t"}))

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING and "hybrid level coordinate" in r.message]
    assert len(warnings) == 1
    assert "missing" in warnings[0].message

    # today's vertical: the coordinate value, no coefficients
    assert len(fields) == 2 * N
    assert sorted(set(f.vertical.level() for f in fields)) == pytest.approx(sorted(lev))
    for f in fields:
        assert type(f.vertical) is Vertical
        assert f.vertical.level_type() == "hybrid"
        assert f.vertical.coefficients() is None


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_without_formula_terms(l137, mode, tmp_path, caplog):
    ds = _cmip6_dataset(l137)
    del ds["lev"].attrs["formula_terms"]
    lev = ds["lev"].values

    with caplog.at_level(logging.DEBUG):
        fl = _read(ds, mode, tmp_path)
        fields = list(fl.sel({"parameter.variable": "t"}))

    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert len(fields) == 2 * N
    assert sorted(set(f.vertical.level() for f in fields)) == pytest.approx(sorted(lev))
    for f in fields:
        assert type(f.vertical) is Vertical
        assert f.vertical.level_type() == "hybrid"
        assert f.vertical.coefficients() is None


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_pressure_levels_unchanged(mode):
    from earthkit.data.utils.testing import load_nc_or_xr_source

    fl = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)
    f = fl[0]
    assert type(f.vertical) is Vertical
    assert f.vertical.level() == 1000
    assert f.vertical.level_type() == "pressure"
    assert f.vertical.coefficients() is None


def test_netcdf_hybrid_decode_coords_all(l137, tmp_path):
    ds = _l137_dataset(l137)
    path = str(tmp_path / "all.nc")
    ds.to_netcdf(path)

    ds2 = xr.open_dataset(path, decode_coords="all")
    try:
        # the formula_terms attribute is in the encoding
        assert "formula_terms" not in ds2["level"].attrs
        assert "formula_terms" in ds2["level"].encoding

        fl = from_object(ds2).to_fieldlist()
        assert len(fl) == 2 * N
        _check_parametric(fl, l137, range(1, N + 1))
    finally:
        ds2.close()


def _count_decode(monkeypatch):
    calls = []
    orig = earthkit.data.field.cf.decode_parametric_vertical

    def decode(ds, coord_name=None):
        calls.append(coord_name)
        return orig(ds, coord_name)

    monkeypatch.setattr(earthkit.data.field.cf, "decode_parametric_vertical", decode)
    return calls


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_decode_once(l137, mode, tmp_path, monkeypatch):
    calls = _count_decode(monkeypatch)

    # two variables share the level coordinate
    fl = _read(_l137_dataset(l137, variables=("t", "u")), mode, tmp_path)
    fields = list(fl)
    assert len(fields) == 4 * N

    assert calls == ["level"]

    A, B = fields[0].vertical.coefficients()
    for f in fields:
        cA, cB = f.vertical.coefficients()
        assert cA is A
        assert cB is B

    # sel with the generic code path, then iterating again
    r = fl.sel({"vertical.level": [3, 4]})
    assert len(r) == 8
    for f in r:
        assert f.vertical.coefficients()[0] is A

    assert calls == ["level"]


def test_netcdf_hybrid_decode_once_variable_sel(l137, monkeypatch):
    """The decoded levels survive Variable.sel and Coordinate.reduced (used by FieldList.sel for big fieldlists)."""
    calls = _count_decode(monkeypatch)

    fl = from_object(_l137_dataset(l137)).to_fieldlist()
    assert calls == ["level"]

    var = fl.variables[0]
    f0 = var[0]
    A, B = f0.vertical.coefficients()

    # select the level
    v1 = var.sel({}, level=7)
    assert v1.length == 2
    for i in range(v1.length):
        f = v1[i]
        assert isinstance(f.vertical, ParametricVertical)
        assert f.vertical.level() == 7
        assert f.vertical.number_of_levels() == N
        assert f.vertical.coefficients()[0] is A
        assert f.vertical.coefficients()[1] is B

    # select the time and then the level
    v2 = var.sel({}, time=np.datetime64("2020-01-01T06:00", "ns"))
    assert v2.length == N
    v3 = v2.sel({}, level=137)
    assert v3.length == 1
    f = v3[0]
    assert isinstance(f.vertical, ParametricVertical)
    assert f.vertical.level() == 137
    assert f.vertical.coefficients()[0] is A

    # without a level selection the (still unreduced) level coordinate is used
    f = v2[4]
    assert f.vertical.level() == 5
    assert f.vertical.coefficients()[0] is A

    assert calls == ["level"]


@pytest.mark.parametrize("mln_first", [False, True])
def test_netcdf_hybrid_precedence_model_level_number(l137, mln_first):
    from earthkit.data.readers.xarray.coordinates import LevelCoordinate

    ds = _cmip6_dataset(l137, with_level_number=True, mln_first=mln_first)
    # both coordinates are level coordinates
    names = list(ds["t"].coords)
    assert names.index("mln") < names.index("lev") if mln_first else names.index("mln") > names.index("lev")

    fl = from_object(ds).to_fieldlist()
    t = [v for v in fl.variables if v.name == "t"][0]
    level_coords = [c.name for c in t.coordinates if isinstance(c, LevelCoordinate)]
    assert sorted(level_coords) == ["lev", "mln"]
    assert level_coords == (["mln", "lev"] if mln_first else ["lev", "mln"])

    # the hybrid coordinate is used whatever the order, the levels come from model_level_number
    sel = fl.sel({"parameter.variable": "t"})
    assert list(dict.fromkeys(_levels(sel))) == list(range(N, 0, -1))
    _check_parametric(fl, l137, range(1, N + 1))


def _positive_dataset(l137, positive):
    """Dataset of the full L137 model stored as a positive "up" model (level 1 at the surface)."""
    A, B = l137
    model = CLS.from_half_levels(A[::-1], B[::-1], positive="up")
    ds = model.encode(coord_values="level_number", ps_dims=None)
    ds = ds.assign_coords(latitude=LAT, longitude=LON)
    ds["t"] = (("level", "latitude", "longitude"), _data(N, 3, 4))
    ds["level"].attrs["positive"] = positive
    return ds


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_shared_coefficients_read_only(l137, mode, tmp_path):
    A, B = l137
    fl = _read(_l137_dataset(l137), mode, tmp_path)
    fields = list(fl)
    assert len(fields) == 2 * N

    cA, cB = fields[0].vertical.coefficients()

    # all the fields share the same arrays, which cannot be changed
    for f in fields:
        a, b = f.vertical.coefficients()
        assert a is cA
        assert b is cB

    for arr in (cA, cB):
        assert not arr.flags.writeable
        with pytest.raises(ValueError, match="read-only"):
            arr[1] = 99.0

    with pytest.raises(ValueError, match="read-only"):
        fields[3].vertical.coefficients()[0][1] = 99.0

    # the other fields (and the GRIB coefficients) are not affected
    for f in fields[::31]:
        a, b = f.vertical.coefficients()
        np.testing.assert_array_equal(a, A)
        np.testing.assert_array_equal(b, B)

    # the shared arrays are not the arrays owned by the model
    assert cA.dtype == np.float64
    assert not np.shares_memory(cA, A)


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_read_only_coefficients_usable(l137, mode, tmp_path):
    import pickle

    A, B = l137
    fl = _read(_l137_dataset(l137), mode, tmp_path)
    f = fl.sel({"vertical.level": 10})[0]
    v = f.vertical
    cA, cB = v.coefficients()
    assert not cA.flags.writeable

    # set, with and without changing the coefficients
    v2 = v.set(level=11)
    assert isinstance(v2, ParametricVertical)
    assert v2.level() == 11
    assert v2.coefficients()[0] is cA
    assert v2.coefficients()[1] is cB

    v3 = v.set(coefficients=(A * 2, B))
    np.testing.assert_array_equal(v3.coefficients()[0], A * 2)
    np.testing.assert_array_equal(cA, A)

    # to_dict
    d = v.to_dict()
    assert d["level"] == 10
    assert d["level_type"] == "hybrid"
    assert d["number_of_levels"] == N

    # pickle
    v4 = pickle.loads(pickle.dumps(v))
    assert isinstance(v4, ParametricVertical)
    assert v4.level() == 10
    assert v4.number_of_levels() == N
    np.testing.assert_array_equal(v4.coefficients()[0], A)
    np.testing.assert_array_equal(v4.coefficients()[1], B)

    # writing a GRIB field with the vertical to GRIB (concatenates the coefficients, no in-place write)
    r = from_source("file", earthkit_test_data_file("ml_data.grib")).to_fieldlist()[0]
    path = str(tmp_path / "out.grib")
    r.set(vertical=v).to_target("file", path)
    w = from_source("file", path).to_fieldlist()[0]
    assert w.vertical.number_of_levels() == N
    np.testing.assert_array_equal(w.vertical.coefficients()[0], A)
    np.testing.assert_array_equal(w.vertical.coefficients()[1], B)
    assert not cA.flags.writeable


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_positive_up(l137, mode, tmp_path, caplog):
    ds = _positive_dataset(l137, "up")
    assert ds["level"].attrs["positive"] == "up"

    with caplog.at_level(logging.DEBUG):
        fl = _read(ds, mode, tmp_path)
        fields = list(fl)

    # positive up is valid CF, so there is no warning (the coefficients are just not rebuilt)
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]

    assert len(fields) == N
    assert [f.vertical.level() for f in fields] == list(range(1, N + 1))
    for f in fields:
        assert f.vertical.level_type() == "hybrid"
        assert type(f.vertical) is Vertical
        assert f.vertical.coefficients() is None


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_hybrid_positive_invalid(l137, mode, tmp_path, caplog):
    ds = _positive_dataset(l137, "sideways")

    with caplog.at_level(logging.WARNING):
        fl = _read(ds, mode, tmp_path)
        fields = list(fl)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING and "hybrid level coordinate" in r.message]
    assert len(warnings) == 1
    assert "sideways" in warnings[0].message

    # today's vertical: the coordinate value, no coefficients
    assert len(fields) == N
    assert [f.vertical.level() for f in fields] == list(range(1, N + 1))
    for f in fields:
        assert f.vertical.level_type() == "hybrid"
        assert type(f.vertical) is Vertical
        assert f.vertical.coefficients() is None
