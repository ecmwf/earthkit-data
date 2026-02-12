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
        {"parameter": {"variable": "t"}, "vertical": {"level": 500}, **prototype},
        {"parameter": {"variable": "t"}, "vertical": {"level": 850}, **prototype},
        {"parameter": {"variable": "u"}, "vertical": {"level": 500}, **prototype},
        {"parameter": {"variable": "u"}, "vertical": {"level": 850}, **prototype},
        {"parameter": {"variable": "d"}, "vertical": {"level": 850}, **prototype},
        {"parameter": {"variable": "d"}, "vertical": {"level": 600}, **prototype},
    ]


@pytest.fixture
def lod_input_data(request):
    return request.param


@pytest.fixture
def lod_distinct_ll_list_values():
    prototype = {
        "geography": {"latitudes": [-10.0, 0.0, 10.0], "longitudes": [20, 40.0]},
        "values": [1, 2, 3, 4, 5, 6],
        "time": {"valid_datetime": "2018-08-01T09:00:00"},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_distinct_ll():
    prototype = {
        "geography": {"latitudes": np.array([-10.0, 0.0, 10.0]), "longitudes": np.array([20, 40.0])},
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "time": {"valid_datetime": "2018-08-01T09:00:00"},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_flat():
    prototype = {
        "geography": {
            "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
            "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        },
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "time": {"valid_datetime": "2018-08-01T09:00:00"},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_flat_invalid():
    prototype = {
        "geography": {
            "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
            "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        },
        "values": np.array([1, 2, 3, 4, 5]),
        "time": {"valid_datetime": "2018-08-01T09:00:00"},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_flat_10x10():
    prototype = {
        "geography": {
            "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
            "longitudes": np.array([20.0, 30.0, 20.0, 30.0, 20.0, 30.0]),
        },
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "time": {"valid_datetime": "2018-08-01T09:00:00"},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_2D_all():
    prototype = {
        "geography": {
            "latitudes": np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
            "longitudes": np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
        },
        "values": np.array([[1, 2], [3, 4], [5, 6]]),
        "time": {"valid_datetime": "2018-08-01T09:00:00"},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_2D_ll():
    prototype = {
        "geography": {
            "latitudes": np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]]),
            "longitudes": np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]]),
        },
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "time": {"valid_datetime": "2018-08-01T09:00:00"},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_2D_values():
    prototype = {
        "geography": {
            "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
            "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        },
        "values": np.array([[1, 2], [3, 4], [5, 6]]),
        "time": {"valid_datetime": "2018-08-01T09:00:00"},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_forecast_1():
    prototype = {
        "geography": {
            "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
            "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        },
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "time": {"base_datetime": "2018-08-01T03:00:00", "step": 6},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_forecast_2():
    prototype = {
        "geography": {
            "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
            "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        },
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "time": {"valid_datetime": "2018-08-01T09:00:00", "step": 6},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_forecast_3():
    prototype = {
        "geography": {
            "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
            "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        },
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "time": {"forecast_reference_time": "2018-08-01T03:00:00", "step": datetime.timedelta(hours=6)},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_ll_forecast_4():
    prototype = {
        "geography": {
            "latitudes": np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0]),
            "longitudes": np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0]),
        },
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "time": {"base_date": 20180801, "base_time": 300, "step": datetime.timedelta(hours=6)},
    }
    return _build_list(prototype)


@pytest.fixture
def lod_no_latlon():
    prototype = {
        "values": np.array([1, 2, 3, 4, 5, 6]),
        "time": {"valid_datetime": "2018-08-01T09:00:00"},
    }
    return _build_list(prototype)


def build_lod_fieldlist(lod, mode):
    from earthkit.data import from_source

    # from earthkit.data.sources.array_list import ArrayField
    from earthkit.data.core.field import Field
    from earthkit.data.indexing.simple import SimpleFieldList

    if mode == "list-of-dicts":
        return from_source("list-of-dicts", lod)
    elif mode == "loop":
        ds = SimpleFieldList()
        for f in lod:
            ds.append(Field.from_dict(f))
        return ds
