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

from earthkit.data.field.handler.labels import SimpleLabels


@pytest.mark.parametrize(
    "_args,_kwargs",
    [
        (({"a": "1", "b": "2"},), {}),
        ((), {"a": "1", "b": "2"}),
        (
            (
                {
                    "a": "1",
                },
            ),
            {"b": "2"},
        ),
    ],
)
def test_field_labels_core(_args, _kwargs):
    labels = SimpleLabels(*_args, **_kwargs)

    assert labels.get("a") == "1"
    assert labels.get("b") == "2"
    assert labels.get("c", "3") == "3"
    assert labels.get("c", default="3") == "3"

    with pytest.raises(KeyError):
        labels.get("c", raise_on_missing=True)

    assert labels.get("a", astype=int) == 1

    assert labels["a"] == "1"
    assert labels["b"] == "2"

    with pytest.raises(KeyError):
        labels["c"]

    assert "a" in labels
    assert "c" not in labels
    assert len(labels) == 2

    keys = list(labels.keys())
    assert keys == ["a", "b"]

    items = list(labels.items())
    assert items == [("a", "1"), ("b", "2")]

    for k1, k2 in zip(labels, ["a", "b"]):
        assert k1 == k2

    for k, v in labels.items():
        assert labels[k] == v

    d = dict(labels)
    assert d == {"a": "1", "b": "2"}


def test_field_labels_from_dict_ok():
    ref = dict(a="1", b="2")

    r = SimpleLabels.from_dict(ref.copy())
    assert r.get("a") == "1"
    assert r.get("b") == "2"


def test_field_labels_from_dict_bad():
    d = dict(a="1", b="2")

    with pytest.raises(TypeError):
        SimpleLabels.from_dict(**d)


@pytest.mark.parametrize(
    "_kwargs, ref", [(dict(a="2"), dict(a="2", b="2")), (dict(c="3"), dict(a="1", b="2", c="3"))]
)
def test_field_labels_set(_kwargs, ref):
    d = dict(a="1", b="2")
    ori_id = id(d)
    labels = SimpleLabels(d)

    r = labels.set(**_kwargs)
    assert r == ref

    # original unchanged
    assert id(d) == ori_id
    assert d == dict(a="1", b="2")
    assert labels == dict(a="1", b="2")
