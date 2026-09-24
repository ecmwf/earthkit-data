# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from importlib.metadata import EntryPoint, EntryPoints

from earthkit.data import from_source, readers
from earthkit.data.readers import matcher
from earthkit.data.utils.testing import earthkit_test_data_file


class PluginReader:
    def __init__(self, data):
        self.data = data

    def mutate(self):
        return self

    def mutate_source(self):
        return self

    def to_data_object(self):
        return "plugin", self.data


@matcher(priority=990)
def match_before_grib(source, path, *, magic=None, deeper_check=False, **kwargs):
    if magic is not None and magic[:4] == b"GRIB":
        return PluginReader(path)


def match_default_priority(source, path, *, magic=None, deeper_check=False, **kwargs):
    return None


@matcher(priority=990)
def match_memory(source, buffer, *, magic=None, deeper_check=False, **kwargs):
    return PluginReader(bytes(buffer))


def _patch_plugins(monkeypatch, plugins):
    """Use ``plugins``, a dict of kind to match functions, instead of the installed plugins."""
    kinds = {group: kind for kind, group in readers.PLUGIN_GROUPS.items()}
    monkeypatch.setattr(readers, "_load_plugins", lambda group: plugins.get(kinds[group], []))
    # the matchers are cached, so build them with the plugins without using the cache
    monkeypatch.setattr(readers, "_matchers", readers._matchers.__wrapped__)


def test_reader_plugin_priority(monkeypatch):
    _patch_plugins(monkeypatch, {"file": [match_before_grib]})
    path = earthkit_test_data_file("chem-cams.grib")
    assert from_source("file", path) == ("plugin", path)


def test_reader_plugin_default_priority(monkeypatch):
    _patch_plugins(monkeypatch, {"file": [match_default_priority]})
    names = [m.__name__ for m in readers._matchers("file")]
    # after the formats identified by magic bytes, before the ones identified by extension
    assert names.index("match_zip") < names.index("match_default_priority") < names.index("match_geojson")


def test_reader_plugin_kind(monkeypatch):
    _patch_plugins(monkeypatch, {"memory": [match_memory]})
    assert "match_memory" not in [m.__name__ for m in readers._matchers("file")]
    assert "match_memory" not in [m.__name__ for m in readers._matchers("stream")]
    assert from_source("memory", b"some data") == ("plugin", b"some data")


def test_reader_plugins_loading(monkeypatch, caplog):
    group = readers.PLUGIN_GROUPS["file"]
    eps = EntryPoints([
        EntryPoint(name="before-grib", value=f"{__name__}:match_before_grib", group=group),
        EntryPoint(name="broken", value="no_such_module:match", group=group),
    ])
    monkeypatch.setattr(readers, "entry_points", lambda group: eps)
    with caplog.at_level(logging.ERROR):
        assert readers._load_plugins(group) == [match_before_grib]
    assert "Cannot load reader plugin 'broken'" in caplog.text


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
