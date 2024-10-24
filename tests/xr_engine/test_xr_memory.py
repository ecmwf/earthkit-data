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

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import load_grib_data  # noqa: E402


class Counter:
    n = 0

    def increment(self):
        self.n += 1

    def get(self):
        return self.n


def count_calls(monkeypatch, cls, method):
    counter = Counter()

    def patched_method(self, *args, **kwargs):
        if not self.released:
            nonlocal counter
            counter.increment()
            return method(self, *args, **kwargs)

    patched_method.__name__ = method.__name__
    monkeypatch.setattr(cls, method.__name__, patched_method)
    return counter


@pytest.mark.cache
@pytest.mark.parametrize(
    "lazy_load,release_source,expected_result",
    [
        (False, False, {"call_count": 0}),
        (False, True, {"call_count": 32}),
        (True, False, {"call_count": 0}),
        (True, True, {"call_count": 0}),
    ],
)
def test_xr_engine_stream_release_source(lazy_load, release_source, expected_result, monkeypatch):
    filename = "test-data/xr_engine/level/pl_small.grib"
    ds_ek, _ = load_grib_data(filename, "url", stream=True)
    ds_ek_ref, _ = load_grib_data(filename, "url", stream=False)

    from earthkit.data.utils.xarray.fieldlist import ReleasableField

    calls_cnt = count_calls(monkeypatch, ReleasableField, ReleasableField._release)

    assert calls_cnt.get() == 0

    kwargs = {
        "lazy_load": lazy_load,
        "release_source": release_source,
    }

    ds = ds_ek.to_xarray(**kwargs)
    assert ds is not None

    assert calls_cnt.get() == expected_result["call_count"]

    # the stream is exhausted
    with pytest.raises(StopIteration):
        next(iter(ds_ek))

    assert np.allclose(
        ds_ek_ref.sel(param="t").order_by(["date", "time", "step", "levelist"]).to_numpy(),
        ds["t"].values.reshape((16, 19, 36)),
    )


@pytest.mark.cache
@pytest.mark.parametrize(
    "lazy_load,release_source,expected_result",
    [
        (False, False, {"call_count": 0, "param": "t"}),
        (False, True, {"call_count": 32, "param": None}),
        (True, False, {"call_count": 0, "param": "t"}),
        (True, True, {"call_count": 0, "param": "t"}),
    ],
)
def test_xr_engine_array_field_release_source(lazy_load, release_source, expected_result, monkeypatch):
    filename = "test-data/xr_engine/level/pl_small.grib"
    ds_ek, _ = load_grib_data(filename, "url", stream=False)
    ds_ek = ds_ek.to_fieldlist()

    from earthkit.data.utils.xarray.fieldlist import ReleasableField

    calls_cnt = count_calls(monkeypatch, ReleasableField, ReleasableField._release)

    assert calls_cnt.get() == 0

    kwargs = {
        "lazy_load": lazy_load,
        "release_source": release_source,
    }

    ds = ds_ek.to_xarray(**kwargs)
    assert ds is not None

    assert calls_cnt.get() == expected_result["call_count"]

    if not lazy_load and release_source:
        with pytest.raises(AttributeError):
            ds_ek[0].metadata("param")
    else:
        assert np.allclose(
            ds_ek.sel(param="t").order_by(["date", "time", "step", "levelist"]).to_numpy(),
            ds["t"].values.reshape((16, 19, 36)),
        )

        assert ds_ek[0].metadata("param") == expected_result["param"]
