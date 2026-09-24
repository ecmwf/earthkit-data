# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from importlib.metadata import entry_points
from typing import TYPE_CHECKING

from earthkit.data.sources.base import Source as Source
from earthkit.data.sources.helpers import (
    _from_ads,
    _from_cds,
    _from_dummy_source,
    _from_ecfs,
    _from_ecmwf_open_data,
    _from_empty,
    _from_fdb,
    _from_file,
    _from_file_pattern,
    _from_forcings,
    _from_gribjump,
    _from_list_of_dicts,
    _from_mars,
    _from_memory,
    _from_multi,
    _from_opendap,
    _from_polytope,
    _from_s3,
    _from_sample,
    _from_stream,
    _from_url,
    _from_url_pattern,
    _from_virtual,
    _from_virtual_directory,
    _from_wekeo,
    _from_wekeo_cds,
    _from_zarr,
)
from earthkit.data.sources.utils import _from_source_instance, _preprocess_name

if TYPE_CHECKING:
    from earthkit.data.data import Data  # type: ignore[import]


POSSIBLE_SOURCES = {
    "file": _from_file,
    "file-pattern": _from_file_pattern,
    "url": _from_url,
    "url-pattern": _from_url_pattern,
    "sample": _from_sample,
    "stream": _from_stream,
    "memory": _from_memory,
    "forcings": _from_forcings,
    "list-of-dicts": _from_list_of_dicts,
    "multi": _from_multi,
    "empty": _from_empty,
    "dummy-source": _from_dummy_source,
    "virtual": _from_virtual,
    "virtual-directory": _from_virtual_directory,
    "ads": _from_ads,
    "cds": _from_cds,
    "ecfs": _from_ecfs,
    "ecmwf-open-data": _from_ecmwf_open_data,
    "fdb": _from_fdb,
    "gribjump": _from_gribjump,
    "mars": _from_mars,
    "opendap": _from_opendap,
    "polytope": _from_polytope,
    "s3": _from_s3,
    "wekeo": _from_wekeo,
    "wekeo-cds": _from_wekeo_cds,
    "zarr": _from_zarr,
}


def from_source(name: str, *args, lazily=False, **kwargs) -> "Data":
    name = _preprocess_name(name)

    if lazily:
        return from_source_lazily(name, *args, **kwargs)

    # Plugins take priority over built-in sources
    plugins = entry_points(group="earthkit.data.sources")
    if name in plugins.names:
        return _from_source_instance(plugins[name].load()(*args, **kwargs))

    if name in POSSIBLE_SOURCES:
        return POSSIBLE_SOURCES[name](*args, **kwargs)

    raise NameError(f"Source '{name}' does not exist.")


def from_source_lazily(name, *args, **kwargs):
    from earthkit.data.utils.lazy import LazySource

    return LazySource(name, *args, **kwargs)
