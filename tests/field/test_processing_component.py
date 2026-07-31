#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import pickle

import pytest

from earthkit.data.field.component.duration import Duration
from earthkit.data.field.component.processing import (
    EmptyProcessingItem,
    EnsembleProcessingItem,
    IncrementingType,
    Processing,
    ProcessingItem,
    ProcessingItemBase,
    ProcessingKind,
    ProcessingMethod,
    TimeProcessingItem,
    get_incrementing_type,
    get_processing_kind,
    get_processing_method,
    item_from_dict,
)

# ===========================================================================
# Enum conversion helpers
# ===========================================================================


@pytest.mark.parametrize(
    "value,ref",
    [
        (ProcessingKind.TIME_PROCESSING, ProcessingKind.TIME_PROCESSING),
        ("time_processing", ProcessingKind.TIME_PROCESSING),
        ("TIME_PROCESSING", ProcessingKind.TIME_PROCESSING),
        ("ensemble_statistics", ProcessingKind.ENSEMBLE_STATISTICS),
    ],
)
def test_processing_get_kind_ok(value, ref):
    assert get_processing_kind(value) == ref


@pytest.mark.parametrize(
    "value,ref",
    [
        (ProcessingMethod.MEAN, ProcessingMethod.MEAN),
        ("maximum", ProcessingMethod.MAXIMUM),
        ("MAXIMUM", ProcessingMethod.MAXIMUM),
        ("standard_deviation", ProcessingMethod.STANDARD_DEVIATION),
    ],
)
def test_processing_get_method_ok(value, ref):
    assert get_processing_method(value) == ref


@pytest.mark.parametrize(
    "value,ref",
    [
        (None, None),
        (IncrementingType.FORECAST_PERIOD, IncrementingType.FORECAST_PERIOD),
        ("forecast_period", IncrementingType.FORECAST_PERIOD),
        ("FORECAST_REFERENCE_TIME", IncrementingType.FORECAST_REFERENCE_TIME),
    ],
)
def test_processing_get_incrementing_ok(value, ref):
    assert get_incrementing_type(value) == ref


@pytest.mark.parametrize("fn", [get_processing_kind, get_processing_method, get_incrementing_type])
def test_processing_get_enum_invalid(fn):
    with pytest.raises(ValueError):
        fn("not-a-valid-value")


# ===========================================================================
# Abstract classes cannot be instantiated
# ===========================================================================


def test_processing_abstract_classes():
    with pytest.raises(TypeError):
        ProcessingItemBase()
    with pytest.raises(TypeError):
        ProcessingItem("time_processing", "mean")


# ===========================================================================
# TimeProcessingItem
# ===========================================================================


def test_processing_time_item_defaults():
    t = TimeProcessingItem()
    assert t.kind() == ProcessingKind.TIME_PROCESSING
    assert t.method() == ProcessingMethod.POINT
    assert t.window_length() is None
    assert t.sampling_frequency() is None
    assert t.incrementing() == IncrementingType.FORECAST_PERIOD
    # accessors that do not apply to a time item return None
    assert t.ensemble_size() is None


def test_processing_time_item_full():
    t = TimeProcessingItem(
        method="maximum",
        window_length="PT6H",
        sampling_frequency="PT1H",
        incrementing="forecast_reference_time",
    )
    assert t.kind() == ProcessingKind.TIME_PROCESSING
    assert t.method() == ProcessingMethod.MAXIMUM
    assert t.window_length() == Duration(hours=6)
    assert t.sampling_frequency() == Duration(hours=1)
    assert t.incrementing() == IncrementingType.FORECAST_REFERENCE_TIME
    assert t.ensemble_size() is None


def test_processing_time_item_window_from_timedelta():
    t = TimeProcessingItem(method="mean", window_length=datetime.timedelta(hours=3))
    assert t.window_length() == Duration(hours=3)


def test_processing_time_item_is_processing_item():
    t = TimeProcessingItem()
    assert isinstance(t, ProcessingItem)
    assert isinstance(t, ProcessingItemBase)


# ===========================================================================
# EnsembleProcessingItem
# ===========================================================================


def test_processing_ensemble_item_defaults():
    e = EnsembleProcessingItem()
    assert e.kind() == ProcessingKind.ENSEMBLE_STATISTICS
    assert e.method() == ProcessingMethod.MEAN
    assert e.ensemble_size() == 0
    # accessors that do not apply to an ensemble item return None
    assert e.window_length() is None
    assert e.sampling_frequency() is None
    assert e.incrementing() is None


def test_processing_ensemble_item_full():
    e = EnsembleProcessingItem(method="standard_deviation", ensemble_size=50)
    assert e.kind() == ProcessingKind.ENSEMBLE_STATISTICS
    assert e.method() == ProcessingMethod.STANDARD_DEVIATION
    assert e.ensemble_size() == 50


def test_processing_ensemble_item_size_coercion():
    e = EnsembleProcessingItem(ensemble_size="7")
    assert e.ensemble_size() == 7
    assert isinstance(e.ensemble_size(), int)


def test_processing_ensemble_item_is_processing_item():
    e = EnsembleProcessingItem()
    assert isinstance(e, ProcessingItem)
    assert isinstance(e, ProcessingItemBase)


# ===========================================================================
# Item key interface (all items expose the full key set)
# ===========================================================================

_ALL_KEYS = {"kind", "method", "window_length", "sampling_frequency", "incrementing", "ensemble_size"}


@pytest.mark.parametrize(
    "item",
    [
        TimeProcessingItem(method="maximum", window_length="PT6H"),
        EnsembleProcessingItem(method="mean", ensemble_size=10),
    ],
)
def test_processing_item_keys(item):
    assert set(item.keys()) == _ALL_KEYS
    for k in _ALL_KEYS:
        assert k in item
    assert "not-a-key" not in item


def test_processing_item_get():
    t = TimeProcessingItem(method="maximum", window_length="PT6H")
    assert t.get("kind") == ProcessingKind.TIME_PROCESSING
    assert t.get("method") == ProcessingMethod.MAXIMUM
    assert t.get("window_length") == Duration(hours=6)
    # applicable-but-absent for this type -> None
    assert t.get("ensemble_size") is None
    # unknown key -> default / raise
    assert t.get("nope") is None
    assert t.get("nope", default="x") == "x"
    with pytest.raises(KeyError):
        t.get("nope", raise_on_missing=True)


def test_processing_item_get_astype():
    e = EnsembleProcessingItem(method="mean", ensemble_size=50)
    assert e.get("ensemble_size", astype=str) == "50"


# ===========================================================================
# Item set() (returns a new item; may change type)
# ===========================================================================


def test_processing_item_set_update():
    t = TimeProcessingItem(method="maximum", window_length="PT6H")
    t2 = t.set(method="minimum")
    assert isinstance(t2, TimeProcessingItem)
    assert t2.method() == ProcessingMethod.MINIMUM
    assert t2.window_length() == Duration(hours=6)
    # original is unchanged
    assert t.method() == ProcessingMethod.MAXIMUM


def test_processing_item_set_no_updates_returns_self():
    t = TimeProcessingItem(method="maximum")
    assert t.set() is t


def test_processing_item_set_changes_type():
    t = TimeProcessingItem(method="maximum", window_length="PT6H")
    e = t.set(kind="ensemble_statistics", method="mean", ensemble_size=10)
    assert isinstance(e, EnsembleProcessingItem)
    assert e.method() == ProcessingMethod.MEAN
    assert e.ensemble_size() == 10


def test_processing_item_set_bad_key():
    t = TimeProcessingItem(method="maximum")
    with pytest.raises(ValueError):
        t.set(not_a_key=1)


# ===========================================================================
# Item serialization / equality / repr / hash / pickle
# ===========================================================================


@pytest.mark.parametrize(
    "item",
    [
        TimeProcessingItem(method="maximum", window_length="PT6H"),
        TimeProcessingItem(
            method="sum",
            window_length="PT1H",
            sampling_frequency="PT30M",
            incrementing="forecast_reference_time",
        ),
        EnsembleProcessingItem(method="mean", ensemble_size=50),
    ],
)
def test_processing_item_to_dict_roundtrip(item):
    d = item.to_dict()
    assert isinstance(d, dict)
    rebuilt = item_from_dict(d)
    assert rebuilt == item
    assert type(rebuilt) is type(item)
    assert hash(rebuilt) == hash(item)


def test_processing_item_from_dict_dispatch():
    t = item_from_dict({"kind": "time_processing", "method": "maximum", "window_length": "PT6H"})
    assert isinstance(t, TimeProcessingItem)
    assert t.window_length() == Duration(hours=6)

    e = item_from_dict({"kind": "ensemble_statistics", "method": "mean", "ensemble_size": 3})
    assert isinstance(e, EnsembleProcessingItem)
    assert e.ensemble_size() == 3

    assert item_from_dict({}) is item_from_dict({})
    assert isinstance(item_from_dict({}), EmptyProcessingItem)


def test_processing_item_equality():
    t1 = TimeProcessingItem(method="maximum", window_length="PT6H")
    t2 = TimeProcessingItem(method="maximum", window_length="PT6H")
    t3 = TimeProcessingItem(method="minimum", window_length="PT6H")
    e = EnsembleProcessingItem(method="maximum")
    assert t1 == t2
    assert t1 != t3
    assert t1 != e
    # equal items are usable in sets/dicts
    assert len({t1, t2}) == 1


def test_processing_item_repr():
    assert "TimeProcessingItem" in repr(TimeProcessingItem(method="maximum"))
    assert "maximum" in repr(TimeProcessingItem(method="maximum"))
    r = repr(EnsembleProcessingItem(method="mean", ensemble_size=50))
    assert "EnsembleProcessingItem" in r
    assert "50" in r


@pytest.mark.parametrize(
    "item",
    [
        TimeProcessingItem(method="maximum", window_length="PT6H"),
        EnsembleProcessingItem(method="mean", ensemble_size=50),
    ],
)
def test_processing_item_pickle(item):
    assert pickle.loads(pickle.dumps(item)) == item


# ===========================================================================
# EmptyProcessingItem
# ===========================================================================


def test_processing_empty_item_accessors():
    em = EmptyProcessingItem()
    assert em.kind() is None
    assert em.method() is None
    assert em.window_length() is None
    assert em.sampling_frequency() is None
    assert em.incrementing() is None
    assert em.ensemble_size() is None


def test_processing_empty_item_get():
    em = EmptyProcessingItem()
    assert em.get("kind") is None
    assert em.get("kind", default="x") == "x"
    with pytest.raises(KeyError):
        em.get("kind", raise_on_missing=True)


def test_processing_empty_item_to_dict_set_repr():
    em = EmptyProcessingItem()
    assert em.to_dict() == {}
    assert repr(em) == "EmptyProcessingItem()"
    with pytest.raises(ValueError):
        em.set(method="mean")


def test_processing_empty_item_equality_and_pickle():
    assert EmptyProcessingItem() == EmptyProcessingItem()
    assert EmptyProcessingItem() != TimeProcessingItem()
    assert pickle.loads(pickle.dumps(EmptyProcessingItem())) == EmptyProcessingItem()


# ===========================================================================
# Processing — tuple interface
# ===========================================================================


def _sample_processing():
    t = TimeProcessingItem(method="maximum", window_length="PT6H")
    e = EnsembleProcessingItem(method="mean", ensemble_size=50)
    return Processing((t, e)), t, e


def test_processing_len_iter_getitem():
    p, t, e = _sample_processing()
    assert len(p) == 2
    assert list(p) == [t, e]
    assert p[0] is t
    assert p[1] is e
    assert p[-1] is e


def test_processing_getitem_out_of_range():
    p, _, _ = _sample_processing()
    assert isinstance(p[9], EmptyProcessingItem)
    assert p[9].kind() is None


def test_processing_getitem_slice():
    p, t, e = _sample_processing()
    s = p[0:1]
    assert isinstance(s, Processing)
    assert len(s) == 1
    assert s[0] is t


def test_processing_getitem_bad_index():
    p, _, _ = _sample_processing()
    with pytest.raises(TypeError):
        p["x"]


def test_processing_add():
    p, t, e = _sample_processing()
    assert len(p + Processing((t,))) == 3
    assert len(p + (e,)) == 3
    assert len(p + [e]) == 3
    assert (p + Processing((t,))) == Processing((t, e, t))


def test_processing_equality_and_hash():
    p, t, e = _sample_processing()
    assert p == Processing((t, e))
    assert p == (t, e)
    assert p != Processing((t,))
    assert isinstance(hash(p), int)
    assert len({p, Processing((t, e))}) == 1


def test_processing_repr():
    p, _, _ = _sample_processing()
    assert repr(p).startswith("Processing(")


# ===========================================================================
# Processing — propagated accessors (return tuples)
# ===========================================================================


def test_processing_propagated_accessors():
    p, _, _ = _sample_processing()
    assert p.kind() == (ProcessingKind.TIME_PROCESSING, ProcessingKind.ENSEMBLE_STATISTICS)
    assert p.method() == (ProcessingMethod.MAXIMUM, ProcessingMethod.MEAN)
    assert p.window_length() == (Duration(hours=6), None)
    assert p.sampling_frequency() == (None, None)
    assert p.incrementing() == (IncrementingType.FORECAST_PERIOD, None)
    assert p.ensemble_size() == (None, 50)


def test_processing_propagated_accessors_empty():
    p = Processing(())
    assert p.kind() == ()
    assert p.method() == ()
    assert p.window_length() == ()
    assert p.ensemble_size() == ()


# ===========================================================================
# Processing — indexed get()
# ===========================================================================


def test_processing_get_indexed_subkey():
    p, _, _ = _sample_processing()
    assert p.get("[0].kind") == ProcessingKind.TIME_PROCESSING
    assert p.get("[0].method") == ProcessingMethod.MAXIMUM
    assert p.get("[0].window_length") == Duration(hours=6)
    assert p.get("[1].ensemble_size") == 50
    # cross-type applicable-but-absent -> None
    assert p.get("[1].window_length") is None


def test_processing_get_indexed_item_dict():
    p, t, _ = _sample_processing()
    assert p.get("[0]") == t.to_dict()


def test_processing_get_indexed_out_of_range():
    p, _, _ = _sample_processing()
    assert p.get("[9].kind") is None
    assert p.get("[9]") is None
    assert p.get("[9]", default="x") == "x"
    with pytest.raises(KeyError):
        p.get("[9]", raise_on_missing=True)


def test_processing_contains_indexed():
    p, _, _ = _sample_processing()
    assert "[0].kind" in p
    assert "[1]" in p


# ===========================================================================
# Processing — set()
# ===========================================================================


def test_processing_set_indexed_update():
    p, _, _ = _sample_processing()
    p2 = p.set({"[0].method": "mean"})
    assert p2[0].method() == ProcessingMethod.MEAN
    assert p2[0].window_length() == Duration(hours=6)
    # original unchanged
    assert p[0].method() == ProcessingMethod.MAXIMUM


def test_processing_set_item_replacement():
    p, _, _ = _sample_processing()
    p2 = p.set({"[0]": {"kind": "time_processing", "method": "sum", "window_length": "PT1H"}})
    assert p2[0].method() == ProcessingMethod.SUM
    assert p2[0].window_length() == Duration(hours=1)


def test_processing_set_full_replacement():
    p, _, _ = _sample_processing()
    p2 = p.set([{"kind": "ensemble_statistics", "method": "mean", "ensemble_size": 3}])
    assert len(p2) == 1
    assert isinstance(p2[0], EnsembleProcessingItem)
    assert p2[0].ensemble_size() == 3


def test_processing_set_no_updates_returns_self():
    p, _, _ = _sample_processing()
    assert p.set() is p


def test_processing_set_plain_key_raises():
    p, _, _ = _sample_processing()
    with pytest.raises(KeyError):
        p.set({"method": "mean"})


def test_processing_set_update_out_of_range_raises():
    p, _, _ = _sample_processing()
    with pytest.raises(KeyError):
        p.set({"[9].method": "mean"})


# ===========================================================================
# Processing — serialization / pickle
# ===========================================================================


def test_processing_to_dict_from_dict_roundtrip():
    p, _, _ = _sample_processing()
    d = p.to_dict()
    assert set(d) == {"items"}
    assert len(d["items"]) == 2
    assert Processing.from_dict(d) == p


def test_processing_from_dict_variants():
    p, t, e = _sample_processing()
    # from a list of item dicts
    assert Processing.from_dict([t.to_dict(), e.to_dict()]) == p
    # empty
    assert Processing.from_dict({}) == Processing(())
    assert Processing.from_dict([]) == Processing(())
    # single item dict (backward compat)
    single = Processing.from_dict(t.to_dict())
    assert len(single) == 1
    assert single[0] == t


def test_processing_pickle():
    p, _, _ = _sample_processing()
    assert pickle.loads(pickle.dumps(p)) == p
