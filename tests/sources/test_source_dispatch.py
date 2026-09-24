# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from importlib.metadata import EntryPoint, EntryPoints

import pytest

from earthkit.data import sources
from earthkit.data.sources import utils


class Plugin(sources.Source):
    def __init__(self, value, *, option=None):
        super().__init__()
        self.value = value
        self.option = option

    def mutate(self):
        return self

    def to_data_object(self):
        return self.value, self.option


def _patch_entry_points(monkeypatch, names):
    eps = EntryPoints(
        EntryPoint(name=name, value=f"{__name__}:Plugin", group="earthkit.data.sources") for name in names
    )
    monkeypatch.setattr(utils, "entry_points", lambda group: eps)


@pytest.mark.parametrize("name", ["custom-source", "file"])
def test_entry_point_plugin(monkeypatch, name):
    _patch_entry_points(monkeypatch, ["custom-source", "file"])
    assert sources.from_source(name, "value", option=42) == ("value", 42)


def test_entry_points_are_cached(monkeypatch):
    calls = []

    def entry_points(group):
        calls.append(group)
        return EntryPoints([])

    monkeypatch.setattr(utils, "entry_points", entry_points)
    for _ in range(3):
        sources.from_source("list-of-dicts", [])
    assert len(calls) == 1


def test_unknown_source_error():
    with pytest.raises(NameError, match="does not exist"):
        sources.from_source("no-such-source")


def test_lazy_source():
    from earthkit.data.utils.lazy import LazySource

    result = sources.from_source("file", "missing.csv", lazily=True)
    assert isinstance(result, LazySource)
