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
from earthkit.data.readers import ReaderPlugin
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


def match_before_grib(source, path, *, magic=None, deeper_check=False, **kwargs):
    if magic is not None and magic[:4] == b"GRIB":
        return PluginReader(path)


def match_nothing(source, data, *, magic=None, deeper_check=False, **kwargs):
    return None


def match_any(source, buffer, *, magic=None, deeper_check=False, **kwargs):
    return PluginReader(bytes(buffer))


before_grib = ReaderPlugin(file=match_before_grib, priority=990)
default_priority = ReaderPlugin(file=match_nothing)
memory_only = ReaderPlugin(memory=match_any, priority=990)


def _patch_plugins(monkeypatch, plugins):
    """Use ``plugins``, a dict of name to ReaderPlugin, instead of the installed plugins."""
    monkeypatch.setattr(readers, "_load_plugins", lambda: plugins)
    # the readers are cached, so build them with the plugins without using the cache
    monkeypatch.setattr(readers, "_readers", readers._readers.__wrapped__)


def test_reader_plugin_priority(monkeypatch):
    _patch_plugins(monkeypatch, {"before-grib": before_grib})
    path = earthkit_test_data_file("chem-cams.grib")
    assert from_source("file", path) == ("plugin", path)


def test_reader_plugin_default_priority(monkeypatch):
    _patch_plugins(monkeypatch, {"new-thing": default_priority})
    names = list(readers._readers())
    # after the formats identified by magic bytes, before the ones identified by extension
    assert names.index("zip") < names.index("new-thing") < names.index("geojson")


def test_reader_plugin_kind(monkeypatch):
    _patch_plugins(monkeypatch, {"memory-only": memory_only})
    assert from_source("memory", b"some data") == ("plugin", b"some data")
    # the plugin is not used for the other kinds of input
    path = earthkit_test_data_file("chem-cams.grib")
    assert from_source("file", path) != ("plugin", path)


def test_reader_plugins_loading(monkeypatch, caplog):
    group = readers.PLUGIN_GROUP
    eps = EntryPoints([
        EntryPoint(name="before-grib", value=f"{__name__}:before_grib", group=group),
        EntryPoint(name="broken", value="no_such_module:plugin", group=group),
        EntryPoint(name="not-a-plugin", value=f"{__name__}:match_nothing", group=group),
    ])
    monkeypatch.setattr(readers, "entry_points", lambda group: eps)
    with caplog.at_level(logging.WARNING):
        assert readers._load_plugins() == {"before-grib": before_grib}
    assert "Cannot load reader plugin 'broken'" in caplog.text
    assert "Cannot load reader plugin 'not-a-plugin'" in caplog.text


def test_reader_plugin_builtin_name(monkeypatch, caplog):
    _patch_plugins(monkeypatch, {"grib": before_grib})
    with caplog.at_level(logging.WARNING):
        assert readers._readers()["grib"] is not before_grib
    assert "Reader plugin 'grib' has the name of a built-in reader" in caplog.text


def test_readers_order():
    priorities = [r.priority for r in readers._readers().values()]
    assert priorities == sorted(priorities, reverse=True)
    assert list(readers._readers())[-1] == "text"


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
