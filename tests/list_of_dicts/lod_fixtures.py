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


def _build_list(prototype):
    return [
        {"param": "t", "levelist": 500, **prototype},
        {"param": "t", "levelist": 850, **prototype},
        {"param": "u", "levelist": 500, **prototype},
        {"param": "u", "levelist": 850, **prototype},
        {"param": "d", "levelist": 850, **prototype},
        {"param": "d", "levelist": 600, **prototype},
    ]


@pytest.fixture
def lod_input_data(request):
    return request.param


@pytest.fixture
def lod_distinct_ll_list_values():
    prototype = {
        "latitudes": [-10.0, 0.0, 10.0],
        "longitudes": [20, 40.0],
        "values": [1, 2, 3, 4, 5, 6],
        "valid_datetime": "2018-08-01T09:00:00",
    }
    return _build_list(prototype)


@pytest.fixture
def lod_distinct_ll():
    prototype = {
        "latitudes": np.array([-10.0, 0.0, 10.0]),
        "longitudes": np.array([20, 40.0]),
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "valid_datetime": "2018-08-01T09:00:00",
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_flat():
    prototype = {
        "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
        "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "valid_datetime": "2018-08-01T09:00:00",
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_flat_invalid():
    prototype = {
        "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
        "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        "values": np.array([1, 2, 3, 4, 5]),
        "valid_datetime": "2018-08-01T09:00:00",
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_flat_10x10():
    prototype = {
        "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
        "longitudes": np.array([20.0, 30.0, 20.0, 30.0, 20.0, 30.0]),
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "valid_datetime": "2018-08-01T09:00:00",
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_2D_all():
    prototype = {
        "latitudes": np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
        "longitudes": np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
        "values": np.array([[1, 2], [3, 4], [5, 6]]),
        "valid_datetime": "2018-08-01T09:00:00",
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_2D_ll():
    prototype = {
        "latitudes": np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
        "longitudes": np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "valid_datetime": "2018-08-01T09:00:00",
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_2D_values():
    prototype = {
        "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
        "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        "values": np.array([[1, 2], [3, 4], [5, 6]]),
        "valid_datetime": "2018-08-01T09:00:00",
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_forecast_1():
    prototype = {
        "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
        "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "base_datetime": "2018-08-01T03:00:00",
        "step": 6,
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_forecast_2():
    prototype = {
        "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
        "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "valid_datetime": "2018-08-01T09:00:00",
        "step": 6,
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_forecast_3():
    prototype = {
        "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
        "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "forecast_reference_time": "2018-08-01T03:00:00",
        "step": datetime.timedelta(hours=6),
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_forecast_4():
    prototype = {
        "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
        "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "date": 20180801,
        "time": 300,
        "step": datetime.timedelta(hours=6),
    }
    return _build_list(prototype)


@pytest.fixture
def lod_no_latlon():
    prototype = {
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "valid_datetime": "2018-08-01T09:00:00",
    }
    return _build_list(prototype)


def build_lod_fieldlist(lod, mode):
    from earthkit.data import from_source
    from earthkit.data.indexing.fieldlist import SimpleFieldList
    from earthkit.data.sources.array_list import ArrayField

    if mode == "list-of-dicts":
        return from_source("list-of-dicts", lod)
    elif mode == "loop":
        ds = SimpleFieldList()
        for f in lod:
            ds.append(ArrayField(f["values"], f))
        return ds
