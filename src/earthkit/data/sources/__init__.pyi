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
#
# The from_source overloads mirror the helper signatures in helpers.py.

from typing import Any, Callable, Literal, Union, overload

import numpy as np

from earthkit.data.core.fieldlist import FieldList
from earthkit.data.data import Data
from earthkit.data.sources.base import Source as Source
from earthkit.data.sources.helpers import Filter, Force, GribHandlePolicy, Paths, Request

POSSIBLE_SOURCES: dict[str, Callable[..., Data]]

@overload
def from_source(
    name: Literal["file"],
    path: Paths,
    expand_user: Union[bool, list, tuple] = True,
    expand_vars: bool = False,
    unix_glob: bool = True,
    recursive_glob: bool = True,
    filter: Filter = None,
    stream: bool = False,
    merger: Any = None,
    parts: Union[list, tuple, None] = None,
    *,
    indexing: bool | None = None,
    grib_handle_policy: GribHandlePolicy | None = None,
    grib_handle_cache_size: int | None = None,
    use_grib_metadata_cache: bool | None = None,
    positions: Any = None,
    skip_warning: bool | None = None,
    content_type: str | None = None,
    **kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["file-pattern"],
    pattern: str,
    *args: dict,
    filter: Filter = None,
    merger: Any = None,
    hive_partitioning: bool = False,
    **pattern_values: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["url"],
    url: Any,
    *,
    update_if_out_of_date: bool = False,
    force: Force = None,
    stream: bool = False,
    chunk_size: int | None = None,
    parts: Union[list, tuple, None] = None,
    filter: Filter = None,
    merger: Any = None,
    verify: bool | None = None,
    range_method: str | None = None,
    http_headers: dict | None = None,
    fake_headers: dict | None = None,
    auth: Any = None,
    session: Any = None,
    indexing: bool | None = None,
    grib_handle_policy: GribHandlePolicy | None = None,
    grib_handle_cache_size: int | None = None,
    use_grib_metadata_cache: bool | None = None,
    positions: Any = None,
    skip_warning: bool | None = None,
    content_type: str | None = None,
    **kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["url-pattern"],
    pattern: str,
    *args: dict,
    filter: Filter = None,
    merger: Any = None,
    force: Force = False,
    **pattern_values: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["sample"],
    path: Paths,
    *,
    update_if_out_of_date: bool | None = None,
    force: Force = None,
    stream: bool | None = None,
    chunk_size: int | None = None,
    parts: Union[list, tuple, None] = None,
    filter: Filter = None,
    merger: Any = None,
    verify: bool | None = None,
    range_method: str | None = None,
    http_headers: dict | None = None,
    fake_headers: dict | None = None,
    auth: Any = None,
    session: Any = None,
    indexing: bool | None = None,
    grib_handle_policy: GribHandlePolicy | None = None,
    grib_handle_cache_size: int | None = None,
    use_grib_metadata_cache: bool | None = None,
    positions: Any = None,
    skip_warning: bool | None = None,
    content_type: str | None = None,
    **kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["stream"],
    stream: Any,
    *,
    use_grib_metadata_cache: bool | None = None,
    skip_warning: bool | None = None,
    content_type: str | None = None,
    **kwargs: Any,
) -> Data: ...
@overload
def from_source(name: Literal["memory"], buf: Union[bytes, bytearray], **kwargs: Any) -> Data: ...
@overload
def from_source(
    name: Literal["forcings"],
    source_or_dataset: Union[Source, FieldList, Data, None] = None,
    *,
    request: dict | None = None,
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(name: Literal["list-of-dicts"], list_of_dicts: list[dict], **kwargs: Any) -> Data: ...
@overload
def from_source(
    name: Literal["multi"], *sources: Any, filter: Filter = None, merger: Any = None, **kwargs: Any
) -> Data: ...
@overload
def from_source(name: Literal["empty"], **kwargs: Any) -> Data: ...
@overload
def from_source(
    name: Literal["dummy-source"],
    kind: str,
    request: dict | None = None,
    force: Force = False,
    extension: str | None = None,
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(name: Literal["virtual"], **request_kwargs: Any) -> Data: ...
@overload
def from_source(name: Literal["virtual-directory"], *args: Any, **kwargs: Any) -> Data: ...
@overload
def from_source(
    name: Literal["ads"],
    dataset: str,
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["cds"],
    dataset: str,
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["ecfs"],
    url: str,
    *,
    force: Force = False,
    filter: Filter = None,
    merger: Any = None,
    parts: Union[list, tuple, None] = None,
    stream: bool = False,
    indexing: bool | None = None,
    grib_handle_policy: GribHandlePolicy | None = None,
    grib_handle_cache_size: int | None = None,
    use_grib_metadata_cache: bool | None = None,
    positions: Any = None,
    skip_warning: bool | None = None,
    content_type: str | None = None,
    **kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["ecmwf-open-data"],
    *args: Request,
    source: str = "ecmwf",
    model: str = "ifs",
    request: Request | None = None,
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["fdb"],
    *args: Request,
    request: Request | None = None,
    stream: bool = True,
    config: Union[dict, str, None] = None,
    userconfig: Union[dict, str, None] = None,
    user_config: Union[dict, str, None] = None,
    lazy: bool = False,
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["gribjump"],
    request: dict,
    *,
    ranges: list[tuple[int, int]] | None = None,
    mask: np.ndarray | None = None,
    indices: np.ndarray | None = None,
    fetch_coords_from_fdb: bool = False,
    fdb_kwargs: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["mars"],
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    log: Union[str, Callable, dict, None] = "default",
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(name: Literal["opendap"], url: str, **kwargs: Any) -> Data: ...
@overload
def from_source(
    name: Literal["polytope"],
    dataset: str,
    *args: Request,
    request: Request | None = None,
    stream: bool = True,
    address: str | None = None,
    user_email: str | None = None,
    user_key: str | None = None,
    **client_kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["s3"],
    *args: Request,
    stream: bool = False,
    anon: bool = True,
    aws_access_key: str | None = None,
    aws_secret_access_key: str | None = None,
    aws_token: str | None = None,
    **kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["wekeo"],
    dataset: str,
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["wekeo-cds"],
    dataset: str,
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(
    name: Literal["wekeocds"],
    dataset: str,
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    **request_kwargs: Any,
) -> Data: ...
@overload
def from_source(name: Literal["zarr"], path: str, **kwargs: Any) -> Data: ...
def from_source_lazily(name, *args, **kwargs): ...
