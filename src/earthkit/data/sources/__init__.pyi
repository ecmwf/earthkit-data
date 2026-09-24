# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# Type stub for this package. Type checkers and editors read only this file for
# ``earthkit.data.sources`` (not ``__init__.py``), so every name defined in
# ``__init__.py`` must also be declared here and kept in sync with it.

from typing import Any, Callable, Literal, Union, overload

import numpy

from earthkit.data.core import Loader
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.data import Data

class Source(Loader):
    name: str | None
    source_filename: str | None
    _kwargs: dict[str, Any]
    _parent: Any
    def __init__(self, **kwargs): ...
    def _cache_file(self, create, args, **kwargs): ...
    @property
    def parent(self): ...
    @parent.setter
    def parent(self, parent): ...
    def _set_parent(self, parent): ...
    def _repr_html_(self): ...
    def graph(self, depth=0): ...
    def to_data_object(self): ...

POSSIBLE_SOURCES: dict[str, Callable[..., Data]]

@overload
def from_source(
    name: Literal["file"],
    path: str,
    expand_user: Union[bool, list, tuple] = True,
    expand_vars: bool = False,
    unix_glob: bool = True,
    recursive_glob: bool = True,
    filter: Union[str, Callable] = None,
    parts: list = None,
    stream: bool = False,
) -> Data: ...
@overload
def from_source(
    name: Literal["file-pattern"], pattern: str, *args, hive_partitioning: bool = False, **kwargs
) -> Data: ...
@overload
def from_source(
    name: Literal["url"],
    url: str,
    unpack: bool = True,
    parts: Union[list, tuple] = None,
    stream: bool = False,
    **kwargs,
) -> Data: ...
@overload
def from_source(name: Literal["url-pattern"], url: str, unpack: bool = True, **kwargs) -> Data: ...
@overload
def from_source(name: Literal["sample"], name_or_path: str) -> Data: ...
@overload
def from_source(name: Literal["stream"], stream: Union[list, tuple]) -> Data: ...
@overload
def from_source(name: Literal["memory"], buffer) -> Data: ...
@overload
def from_source(
    name: Literal["forcings"], source_or_dataset=Union[Source, FieldList], *, request: dict = {}, **kwargs
) -> Data: ...
@overload
def from_source(name: Literal["list-of-dicts"], list_of_dicts: list[dict]) -> Data: ...
@overload
def from_source(
    name: Literal["multi"], *sources, merger: Union[str, Callable, tuple[str, dict], Any], **kwargs
) -> Data: ...
@overload
def from_source(name: Literal["empty"]) -> Data: ...
@overload
def from_source(
    name: Literal["dummy-source"],
    kind: str,
    request: dict = None,
    force: bool = False,
    extension: str = None,
    **kwargs,
) -> Data: ...
@overload
def from_source(name: Literal["virtual"], **kwargs) -> Data: ...
@overload
def from_source(name: Literal["virtual-directory"], *args, **kwargs) -> Data: ...
@overload
def from_source(
    name: Literal["ads"], dataset: str, *args, request: Union[dict, list[dict], tuple[dict]] = None, **kwargs
) -> Data: ...
@overload
def from_source(
    name: Literal["cds"],
    dataset: str,
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    **kwargs,
) -> Data: ...
@overload
def from_source(name: Literal["ecfs"], path: str) -> Data: ...
@overload
def from_source(
    name: Literal["ecmwf-open-data"],
    *args,
    source: Literal["azure", "ecmwf"] = "ecmwf",
    model: Literal["ifs", "aifs"] = "ifs",
    request: Union[dict, list[dict], tuple[dict]] = None,
    **kwargs,
) -> Data: ...
@overload
def from_source(
    name: Literal["fdb"],
    *args,
    config: Union[dict, str] = None,
    userconfig: Union[dict, str] = None,
    request: Union[dict, list[dict], tuple[dict]] = None,
    stream: bool = True,
    lazy: bool = False,
    **kwargs,
) -> Data: ...
@overload
def from_source(
    name: Literal["gribjump"],
    request: Union[dict, list[dict], tuple[dict]] = None,
    *,
    ranges: list[tuple[int, int]] = None,
    mask: numpy.ndarray = None,
    indices: numpy.ndarray = None,
    fetch_coords_from_fdb: bool = False,
    fdb_kwargs: dict = None,
    **kwargs,
) -> Data: ...
@overload
def from_source(
    name: Literal["mars"],
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    log: Union[str, Callable, dict, None] = "default",
    **kwargs,
) -> Data: ...
@overload
def from_source(name: Literal["opendap"], url: str) -> Data: ...
@overload
def from_source(
    name: Literal["polytope"],
    collection: str,
    *args,
    address: str = None,
    user_email: str = None,
    user_key: str = None,
    request: Union[dict, list[dict], tuple[dict]] = None,
    stream: bool = True,
    **kwargs,
) -> Data: ...
@overload
def from_source(
    name: Literal["s3"],
    *args,
    anon: bool = True,
    aws_access_key: str = None,
    aws_secret_access_key: str = None,
    aws_token: str = None,
    stream: bool = True,
) -> Data: ...
@overload
def from_source(
    name: Literal["wekeo"],
    dataset: str,
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    **kwargs,
) -> Data: ...
@overload
def from_source(
    name: Literal["wekeocds"],
    dataset: str,
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    **kwargs,
) -> Data: ...
@overload
def from_source(
    name: Literal["wekeo-cds"],
    dataset: str,
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    **kwargs,
) -> Data: ...
@overload
def from_source(
    name: Literal["zarr"],
    path: str,
) -> Data: ...
def _from_source_instance(src: Source) -> Data: ...
def from_source_lazily(name, *args, **kwargs): ...
