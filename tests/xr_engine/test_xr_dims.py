#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data.utils.xarrayengine import MarsProfile

SAMPLE_DATA_FOLDER = "~/git/cfgrib/tests/sample-data"
SAMPLE_DATA_FOLDER = "/Users/cgr/metview/python_test/earthkit_data/engine"

DS_LEV = {
    "class": ["od"],
    "param": ["t", "r"],
    "levelist": [1000, 850],
    "level": [1000, 850],
    "time": ["12"],
    "step": [0],
}

DS_DATE_LEV = {
    "class": ["od"],
    "param": ["t", "r"],
    "shortName": ["t", "r"],
    "levelist": [1000, 850],
    "level": [1000, 850],
    "levtype": ["pl"],
    "date": ["20210101", "20210102"],
    "time": ["12"],
    "step": [0],
    "base_datetime": ["2021-01-01T12:00:00", "2021-01-02T12:00:00"],
}


class ProductJoiner:
    def __init__(self, func):
        self.func = func

    def format_name(self, x, **kwargs):
        return self.func(x, **kwargs)

    def format_string(self, x):
        return str(x)

    def join(self, args):
        lst = []
        for x in args:
            if isinstance(x, list):
                lst.append([str(v) for v in x])
            if isinstance(x, str) and x:
                lst.append([x])

        from itertools import product

        return ["".join(x) for x in list(product(*lst))]


class DS:
    def __init__(self, data, remapping=None):
        self.data = dict(data)
        self.remapping = remapping
        if not remapping:
            remapping = {}
        assert isinstance(remapping, dict)

        if "param_level" not in remapping:
            remapping["param_level"] = "{param}{level}"
        if "level_and_type" not in remapping:
            remapping["level_and_type"] = "{level}{levtype}"

        if remapping:
            from earthkit.data.core.order import build_remapping

            remapping = build_remapping(remapping)
            self._index_values = remapping(self.index_values, joiner=ProductJoiner)
        else:
            self._index = self._index_values

    def index(self, key):
        v = self._index_values(key)
        if key not in self.data:
            self.data[key] = v
        return v

    def indices(self):
        return self.data

    def index_values(self, key):
        return sorted(self.data.get(key, []))

    def attributes(self):
        return {k: v[0] for k, v in self.indices().items() if len(v) == 1}

    def load(self, keys):
        for k in keys:
            self.index(k)


def test_xr_dims_mock_ds():
    ds = DS(DS_DATE_LEV)
    assert ds.index("param") == ["r", "t"]
    assert ds.index("param_level") == ["r850", "r1000", "t850", "t1000"]
    assert ds.index("level_and_type") == ["850pl", "1000pl"]

    ds = DS(DS_DATE_LEV, remapping={"param_level": "{param}_{level}"})
    assert ds.index("param") == ["r", "t"]
    assert ds.index("param_level") == ["r_850", "r_1000", "t_850", "t_1000"]

    ds = DS(
        DS_DATE_LEV,
        remapping={
            "param_level": "{param}_{level}",
            "level_and_type": "{level}_{levtype}",
        },
    )
    assert ds.index("param") == ["r", "t"]
    assert ds.index("param_level") == ["r_850", "r_1000", "t_850", "t_1000"]
    assert ds.index("level_and_type") == ["850_pl", "1000_pl"]


@pytest.mark.parametrize(
    "kwargs,variable_key,variables,dim_keys",
    [
        ({}, "param", ["r", "t"], ["levelist"]),
        ({"use_base_datetime": True}, "param", ["r", "t"], ["levelist"]),
    ],
)
def test_xr_dims_ds_lev(kwargs, variable_key, variables, dim_keys):
    prof = MarsProfile(**kwargs)
    ds = DS(DS_LEV)
    prof.update(ds, ds.attributes())
    assert prof.variable_key == variable_key
    assert prof.variables == variables
    assert prof.dim_keys == dim_keys


@pytest.mark.parametrize(
    "kwargs,variable_key,variables,dims",
    [
        ({}, "param", ["r", "t"], ["date", "levelist"]),
        (
            {"use_base_datetime": True},
            "param",
            ["r", "t"],
            ["base_datetime", "levelist"],
        ),
        (
            {"variable_key": "param_level"},
            "param_level",
            ["r850", "r1000", "t850", "t1000"],
            ["date"],
        ),
        (
            {"extra_index_keys": "param_level"},
            "param_level",
            ["r850", "r1000", "t850", "t1000"],
            ["date"],
        ),
        (
            {"remapping": {"param_level": "{param}_{level}"}},
            "param_level",
            ["r_850", "r_1000", "t_850", "t_1000"],
            ["date"],
        ),
        (
            {"variable_key": "shortName"},
            "shortName",
            ["r", "t"],
            ["date", "levelist"],
        ),
        (
            {"variable_key": "shortName", "drop_variables": ["r"]},
            "shortName",
            ["t"],
            ["date", "levelist"],
        ),
        (
            {"variable_key": "param_level", "drop_variables": ["r", "r1000"]},
            "param_level",
            ["r850", "t850", "t1000"],
            ["date"],
        ),
        # (
        #     {"use_level_per_type_dim": True},
        #     "param",
        #     ["r", "t"],
        #     {"date": ["20210101", "20210102"], "level_per_type": ["850pl", "1000pl"]},
        # ),
        (
            {"extra_index_keys": "level_and_type"},
            "param",
            ["r", "t"],
            {"date": ["20210101", "20210102"], "level_and_type": ["850pl", "1000pl"]},
        ),
    ],
)
def test_xr_dims_ds_date_lev(kwargs, variable_key, variables, dims):

    remapping = None
    if "remapping" in kwargs:
        remapping = dict(kwargs["remapping"])

    prof = MarsProfile(**kwargs)
    ds = DS(DS_DATE_LEV, remapping=remapping)
    ds.load(prof.index_keys)
    prof.update(ds, ds.attributes())
    assert prof.variable_key == variable_key
    assert prof.variables == variables

    if isinstance(dims, list):
        assert prof.dim_keys == dims
    elif isinstance(dims, dict):
        assert len(prof.dim_keys) == len(dims)
        for k in prof.dim_keys:
            assert ds.index(k) == dims[k]
    else:
        raise ValueError(f"Unsupported dims: {dims}")
