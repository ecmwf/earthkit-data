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

from earthkit.data.xr_engine.diff import DictDiff, ListDiff


def test_xr_engine_diff_list_same():
    diff = ListDiff.diff([1, 2, 3], [1, 2, 3])
    assert diff.same
    assert diff.diff_index == -1


def test_xr_engine_diff_list_length_mismatch():
    diff = ListDiff.diff([1, 2, 3], [1, 2])
    assert not diff.same
    assert "Length mismatch: 3 != 2" in diff.diff_text
    assert diff.diff_index == -1


def test_xr_engine_diff_list_value_mismatch():
    diff = ListDiff.diff([1, 2, 3], [1, 5, 3])
    assert not diff.same
    assert diff.diff_index == 1
    assert "Value mismatch at level[1]: 2 != 5" in ListDiff.diff([1, 2, 3], [1, 5, 3], name="level").diff_text


def test_xr_engine_diff_list_type_mismatch():
    diff = ListDiff.diff([1, 2, 3], [1, "b", 3])
    assert not diff.same
    assert diff.diff_index == 1
    assert "Type mismatch at level[1]" in ListDiff.diff([1, 2, 3], [1, "b", 3], name="level").diff_text


@pytest.mark.parametrize(
    "vals1,vals2",
    [
        ([1, 2, 3], [np.int64(1), np.int64(2), np.int64(3)]),
        ([1.0, 2.0, 3.0], [np.float32(1.0), np.float32(2.0), np.float32(3.0)]),
        ([1, 2, 3], [1.0, 2.0, 3.0]),
        ([None], [None]),
    ],
)
def test_xr_engine_diff_list_numeric_cross_type_same(vals1, vals2):
    diff = ListDiff.diff(vals1, vals2)
    assert diff.same


@pytest.mark.parametrize("vals1,vals2", [(1, [1]), ([1], 1), ({"a": 1}, [1]), ([1], {"a": 1})])
def test_xr_engine_diff_list_invalid_type_raises(vals1, vals2):
    with pytest.raises(ValueError):
        ListDiff.diff(vals1, vals2)


def test_xr_engine_diff_dict_same():
    diff = DictDiff.diff({"a": 1, "b": 2}, {"a": 1, "b": 2})
    assert diff.same
    assert diff.diff_dict == {}


def test_xr_engine_diff_dict_flattens_nested():
    vals1 = {"a": 1, "b": {"c": 2, "d": 3}}
    vals2 = {"a": 1, "b": {"c": 2, "d": 3}}
    diff = DictDiff.diff(vals1, vals2)
    assert diff.same


def test_xr_engine_diff_dict_value_mismatch():
    diff = DictDiff.diff({"a": 1, "b": 2}, {"a": 1, "b": 5})
    assert not diff.same
    assert diff.diff_dict == {"b": (5, 2)}
    assert "b: 5 != 2" in diff.diff_text


def test_xr_engine_diff_dict_nested_value_mismatch():
    vals1 = {"a": 1, "b": {"c": 2}}
    vals2 = {"a": 1, "b": {"c": 5}}
    diff = DictDiff.diff(vals1, vals2)
    assert not diff.same
    assert diff.diff_dict == {"b.c": (5, 2)}


def test_xr_engine_diff_dict_missing_key():
    diff = DictDiff.diff({"a": 1, "b": 2}, {"a": 1, "c": 2})
    assert not diff.same
    assert diff.diff_dict == {"b": (None, 2)}


def test_xr_engine_diff_dict_length_mismatch():
    diff = DictDiff.diff({"a": 1, "b": 2}, {"a": 1})
    assert not diff.same
    assert "Length mismatch: 2 != 1" in diff.diff_text


@pytest.mark.parametrize("vals1,vals2", [(1, {"a": 1}), ({"a": 1}, 1), ([1], {"a": 1}), ({"a": 1}, [1])])
def test_xr_engine_diff_dict_invalid_type_raises(vals1, vals2):
    with pytest.raises(ValueError):
        DictDiff.diff(vals1, vals2)


@pytest.mark.parametrize(
    "vals1,vals2",
    [
        ({"a": 1}, {"a": np.int64(1)}),
        ({"a": 1.0}, {"a": np.float32(1.0)}),
        ({"a": 1}, {"a": 1.0}),
    ],
)
def test_xr_engine_diff_dict_numeric_cross_type_same(vals1, vals2):
    diff = DictDiff.diff(vals1, vals2)
    assert diff.same
