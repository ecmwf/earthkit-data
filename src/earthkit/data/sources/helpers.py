# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Literal, Union

from earthkit.data.sources.utils import _from_source_instance

if TYPE_CHECKING:
    import numpy as np

    from earthkit.data.core.fieldlist import FieldList
    from earthkit.data.data import Data  # type: ignore[import]
    from earthkit.data.sources import Source

Request = Union[dict, list[dict], tuple[dict, ...]]
Paths = Union[str, list[str], tuple[str, ...]]
Filter = Union[str, Callable, None]
Force = Union[bool, Callable, None]
GribHandlePolicy = Literal["cache", "persistent", "temporary"]


def _given(**kwargs: Any) -> dict[str, Any]:
    """Return the keyword arguments that are not None.

    Used for options the source classes do not take themselves but forward to other
    objects (e.g. readers), which would warn about receiving them.
    """
    return {k: v for k, v in kwargs.items() if v is not None}


def _to_data(src: Source, name: str) -> Data:
    # The name must be set after the source is created, since some sources use the
    # class-derived name as the cache owner when retrieving data in __init__
    if getattr(src, "name", None) is None:
        src.name = name
    return _from_source_instance(src)


def _from_file(
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
) -> Data:
    from earthkit.data.sources.file import File

    src = File(
        path,
        expand_user=expand_user,
        expand_vars=expand_vars,
        unix_glob=unix_glob,
        recursive_glob=recursive_glob,
        filter=filter,
        stream=stream,
        merger=merger,
        parts=parts,
        **_given(
            indexing=indexing,
            grib_handle_policy=grib_handle_policy,
            grib_handle_cache_size=grib_handle_cache_size,
            use_grib_metadata_cache=use_grib_metadata_cache,
            positions=positions,
            skip_warning=skip_warning,
            content_type=content_type,
        ),
        **kwargs,
    )
    return _to_data(src, "file")


def _from_file_pattern(
    pattern: str,
    *args: dict,
    filter: Filter = None,
    merger: Any = None,
    hive_partitioning: bool = False,
    **pattern_values: Any,
) -> Data:
    from earthkit.data.sources.file_pattern import FilePattern

    src = FilePattern(
        pattern, *args, filter=filter, merger=merger, hive_partitioning=hive_partitioning, **pattern_values
    )
    return _to_data(src, "file-pattern")


def _from_url(
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
) -> Data:
    from earthkit.data.sources.url import Url

    src = Url(
        url,
        update_if_out_of_date=update_if_out_of_date,
        force=force,
        stream=stream,
        **_given(
            chunk_size=chunk_size,
            parts=parts,
            filter=filter,
            merger=merger,
            verify=verify,
            range_method=range_method,
            http_headers=http_headers,
            fake_headers=fake_headers,
            auth=auth,
            session=session,
            indexing=indexing,
            grib_handle_policy=grib_handle_policy,
            grib_handle_cache_size=grib_handle_cache_size,
            use_grib_metadata_cache=use_grib_metadata_cache,
            positions=positions,
            skip_warning=skip_warning,
            content_type=content_type,
        ),
        **kwargs,
    )
    return _to_data(src, "url")


def _from_url_pattern(
    pattern: str,
    *args: dict,
    filter: Filter = None,
    merger: Any = None,
    force: Force = False,
    **pattern_values: Any,
) -> Data:
    from earthkit.data.sources.url_pattern import UrlPattern

    src = UrlPattern(pattern, *args, filter=filter, merger=merger, force=force, **pattern_values)
    return _to_data(src, "url-pattern")


def _from_sample(
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
) -> Data:
    from earthkit.data.sources.sample import Sample

    # Sample passes its keyword arguments on to the url source
    src = Sample(
        path,
        **_given(
            update_if_out_of_date=update_if_out_of_date,
            force=force,
            stream=stream,
            chunk_size=chunk_size,
            parts=parts,
            filter=filter,
            merger=merger,
            verify=verify,
            range_method=range_method,
            http_headers=http_headers,
            fake_headers=fake_headers,
            auth=auth,
            session=session,
            indexing=indexing,
            grib_handle_policy=grib_handle_policy,
            grib_handle_cache_size=grib_handle_cache_size,
            use_grib_metadata_cache=use_grib_metadata_cache,
            positions=positions,
            skip_warning=skip_warning,
            content_type=content_type,
        ),
        **kwargs,
    )
    return _to_data(src, "sample")


def _from_stream(
    stream: Any,
    *,
    use_grib_metadata_cache: bool | None = None,
    skip_warning: bool | None = None,
    content_type: str | None = None,
    **kwargs: Any,
) -> Data:
    from earthkit.data.sources.stream import StreamSource

    src = StreamSource(
        stream,
        **_given(
            use_grib_metadata_cache=use_grib_metadata_cache,
            skip_warning=skip_warning,
            content_type=content_type,
        ),
        **kwargs,
    )
    return _to_data(src, "stream")


def _from_memory(buf: Union[bytes, bytearray], **kwargs: Any) -> Data:
    from earthkit.data.sources.memory import MemorySource

    return _to_data(MemorySource(buf, **kwargs), "memory")


def _from_forcings(
    source_or_dataset: Union[Source, FieldList, Data, None] = None,
    *,
    request: dict | None = None,
    **request_kwargs: Any,
) -> Data:
    from earthkit.data.sources.forcings import ForcingsFieldList

    src = ForcingsFieldList(source_or_dataset, request={} if request is None else request, **request_kwargs)
    return _to_data(src, "forcings")


def _from_list_of_dicts(list_of_dicts: list[dict], **kwargs: Any) -> Data:
    from earthkit.data.sources.list_of_dicts import FieldlistFromDicts

    return _to_data(FieldlistFromDicts(list_of_dicts, **kwargs), "list-of-dicts")


def _from_multi(*sources: Any, filter: Filter = None, merger: Any = None, **kwargs: Any) -> Data:
    from earthkit.data.sources.multi import MultiSource

    return _to_data(MultiSource(*sources, filter=filter, merger=merger, **kwargs), "multi")


def _from_empty(**kwargs: Any) -> Data:
    from earthkit.data.sources.empty import EmptySource

    return _to_data(EmptySource(**kwargs), "empty")


def _from_dummy_source(
    kind: str,
    request: dict | None = None,
    force: Force = False,
    extension: str | None = None,
    **request_kwargs: Any,
) -> Data:
    from earthkit.data.sources.dummy_source import DummySource

    src = DummySource(kind, request=request, force=force, extension=extension, **request_kwargs)
    return _to_data(src, "dummy-source")


def _from_virtual(**request_kwargs: Any) -> Data:
    from earthkit.data.sources.virtual import Virtual

    return _to_data(Virtual(**request_kwargs), "virtual")


def _from_virtual_directory(*args: Any, **kwargs: Any) -> Data:
    # The signature is defined by DirectorySource, which no longer exists
    from earthkit.data.sources.virtual_directory import VirtualDirectorySource

    return _to_data(VirtualDirectorySource(*args, **kwargs), "virtual-directory")


def _from_ads(
    dataset: str,
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    **request_kwargs: Any,
) -> Data:
    from earthkit.data.sources.ads import ADSRetriever

    src = ADSRetriever(dataset, *args, request=request, prompt=prompt, **request_kwargs)
    return _to_data(src, "ads")


def _from_cds(
    dataset: str,
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    **request_kwargs: Any,
) -> Data:
    from earthkit.data.sources.cds import CDSRetriever

    src = CDSRetriever(dataset, *args, request=request, prompt=prompt, **request_kwargs)
    return _to_data(src, "cds")


def _from_ecfs(
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
) -> Data:
    from earthkit.data.sources.ecfs import ECFSRetriever

    src = ECFSRetriever(
        url,
        force=force,
        filter=filter,
        merger=merger,
        parts=parts,
        stream=stream,
        **_given(
            indexing=indexing,
            grib_handle_policy=grib_handle_policy,
            grib_handle_cache_size=grib_handle_cache_size,
            use_grib_metadata_cache=use_grib_metadata_cache,
            positions=positions,
            skip_warning=skip_warning,
            content_type=content_type,
        ),
        **kwargs,
    )
    return _to_data(src, "ecfs")


def _from_ecmwf_open_data(
    *args: Request,
    source: str = "ecmwf",
    model: str = "ifs",
    request: Request | None = None,
    **request_kwargs: Any,
) -> Data:
    from earthkit.data.sources.ecmwf_open_data import EODRetriever

    src = EODRetriever(*args, source=source, model=model, request=request, **request_kwargs)
    return _to_data(src, "ecmwf-open-data")


def _from_fdb(
    *args: Request,
    request: Request | None = None,
    stream: bool = True,
    config: Union[dict, str, None] = None,
    userconfig: Union[dict, str, None] = None,
    user_config: Union[dict, str, None] = None,
    lazy: bool = False,
    **request_kwargs: Any,
) -> Data:
    from earthkit.data.sources.fdb import FDBSource

    src = FDBSource(
        *args,
        request=request,
        stream=stream,
        config=config,
        userconfig=userconfig,
        user_config=user_config,
        lazy=lazy,
        **request_kwargs,
    )
    return _to_data(src, "fdb")


def _from_gribjump(
    request: dict,
    *,
    ranges: list[tuple[int, int]] | None = None,
    mask: np.ndarray | None = None,
    indices: np.ndarray | None = None,
    fetch_coords_from_fdb: bool = False,
    fdb_kwargs: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Data:
    from earthkit.data.sources.gribjump import GribJumpSource

    src = GribJumpSource(
        request,
        ranges=ranges,
        mask=mask,
        indices=indices,
        fetch_coords_from_fdb=fetch_coords_from_fdb,
        fdb_kwargs=fdb_kwargs,
        **kwargs,
    )
    return _to_data(src, "gribjump")


def _from_mars(
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    log: Union[str, Callable, dict, None] = "default",
    **request_kwargs: Any,
) -> Data:
    from earthkit.data.sources.mars import MARSRetriever

    src = MARSRetriever(*args, request=request, prompt=prompt, log=log, **request_kwargs)
    return _to_data(src, "mars")


def _from_opendap(url: str, **kwargs: Any) -> Data:
    from earthkit.data.sources.opendap import OpenDAP

    return _to_data(OpenDAP(url, **kwargs), "opendap")


def _from_polytope(
    dataset: str,
    *args: Request,
    request: Request | None = None,
    stream: bool = True,
    address: str | None = None,
    user_email: str | None = None,
    user_key: str | None = None,
    **client_kwargs: Any,
) -> Data:
    from earthkit.data.sources.polytope import Polytope

    # All the remaining keyword arguments are passed to polytope.api.Client
    src = Polytope(
        dataset,
        *args,
        request=request,
        stream=stream,
        **_given(address=address, user_email=user_email, user_key=user_key),
        **client_kwargs,
    )
    return _to_data(src, "polytope")


def _from_s3(
    *args: Request,
    stream: bool = False,
    anon: bool = True,
    aws_access_key: str | None = None,
    aws_secret_access_key: str | None = None,
    aws_token: str | None = None,
    **kwargs: Any,
) -> Data:
    from earthkit.data.sources.s3 import S3Source

    src = S3Source(
        *args,
        stream=stream,
        anon=anon,
        aws_access_key=aws_access_key,
        aws_secret_access_key=aws_secret_access_key,
        aws_token=aws_token,
        **kwargs,
    )
    return _to_data(src, "s3")


def _from_wekeo(
    dataset: str,
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    **request_kwargs: Any,
) -> Data:
    from earthkit.data.sources.wekeo import WekeoRetriever

    src = WekeoRetriever(dataset, *args, request=request, prompt=prompt, **request_kwargs)
    return _to_data(src, "wekeo")


def _from_wekeo_cds(
    dataset: str,
    *args: Request,
    request: Request | None = None,
    prompt: bool = True,
    **request_kwargs: Any,
) -> Data:
    from earthkit.data.sources.wekeo_cds import WekeoCDSRetriever

    src = WekeoCDSRetriever(dataset, *args, request=request, prompt=prompt, **request_kwargs)
    return _to_data(src, "wekeo-cds")


def _from_zarr(path: str, **kwargs: Any) -> Data:
    from earthkit.data.sources.zarr import ZarrSource

    return _to_data(ZarrSource(path, **kwargs), "zarr")
