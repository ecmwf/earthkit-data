# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

try:
    import pygribjump as pygj
except ImportError:
    raise ImportError("GribJump access requires 'pygribjump' to be installed")

import dataclasses
import itertools
import os
from collections import UserList
from typing import Any
from typing import Optional

import numpy as np

from earthkit.data.indexing.fieldlist import SimpleFieldList
from earthkit.data.readers.grib.metadata import GribMetadata
from earthkit.data.sources import Source
from earthkit.data.sources.array_list import ArrayField
from earthkit.data.sources.fdb import FDBRetriever
from earthkit.data.utils.metadata.dict import UserMetadata


def split_mars_requests(request: dict[str, Any]) -> list[dict[str, Any]]:
    """Splits a MARS request into individual single-field requests by expanding list values.

    Creates all possible combinations of list values in the request dictionary,
    generating separate requests for each field. This is required because GribJump
    returns result arrays without metadata, so each field must be requested individually
    to map outputs correctly.

    NOTE: Parsing of MARS requests should ideally not be handled here but in a dedicated
    component like pymetkit. Consider updating this function once something appropriate
    is available.

    Parameters
    ----------
    request : dict[str, Any]
        The request dictionary containing MARS keywords with potentially list values.
        List keys are sorted alphabetically to ensure deterministic ordering.

    Returns
    -------
    list[dict[str, Any]]
        A list of individual request dictionaries, each representing a single field.

    Raises
    ------
    ValueError
        If the request contains unsupported "/" syntax for lists/ranges or empty lists.
    TypeError
        If list values contain mixed types.

    Examples
    --------
    >>> split_mars_requests({"param": ["2t", "msl"], "date": "20230101"})
    [{'param': '2t', 'date': '20230101'}, {'param': 'msl', 'date': '20230101'}]

    >>> split_mars_requests({"param": ["2t", "msl"], "step": [0, 6]})
    [{'param': '2t', 'step': 0}, {'param': '2t', 'step': 6},
     {'param': 'msl', 'step': 0}, {'param': 'msl', 'step': 6}]
    """
    request = request.copy()

    # Validate request values
    for k in request.keys():
        v = request[k]
        if isinstance(v, str) and "/" in v:
            raise ValueError(
                f"Found unsupported list or range using '/' in value '{v}' for keyword '{k}'. "
                "Use Python lists to load from multiple fields."
            )
        elif isinstance(v, list) and len(v) == 0:
            raise ValueError(f"Cannot expand dictionary with empty list. " f"Found empty list for key '{k}'.")
        elif isinstance(v, list) and len({type(v_) for v_ in v}) != 1:
            raise TypeError(
                f"All list values must share the same type but found types {set(map(type, v))} " f"in {k}={v}"
            )

    list_keywords = sorted(k for k, v in request.items() if isinstance(v, list))
    lists = [request[k] for k in list_keywords]

    expanded_requests = []
    for combination in itertools.product(*lists):
        new_request = request.copy()
        for k, v in zip(list_keywords, combination):
            new_request[k] = v
        expanded_requests.append(new_request)
    return expanded_requests


def mask_to_ranges(mask: np.ndarray) -> list[tuple[int, int]]:
    """Converts a boolean mask to ranges of indices where the mask is True.

    Parameters
    ----------
    mask : np.ndarray
        A 1D boolean numpy array.

    Returns
    -------
    list[tuple[int, int]]
        A list of tuples representing the start and end indices of True segments in the mask.
    """
    if not isinstance(mask, np.ndarray):
        raise TypeError(f"Expected 'mask' to be a numpy array, got {type(mask)}")
    if not np.issubdtype(mask.dtype, np.bool_):
        raise ValueError(f"Expected 'mask' to be a boolean array, got {mask.dtype}")
    if mask.ndim != 1:
        # NOTE: We could relax this and allow 2D masks, which we flatten using .ravel().
        raise ValueError(f"Expected 'mask' to be a 1D numpy array, got {mask.ndim}D")

    padded = np.concatenate(([False], mask, [False]))
    d = np.diff(padded.astype(int))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]

    ranges = list(zip(starts, ends))
    return ranges


@dataclasses.dataclass
class ExtractionRequest:
    """
    Simple wrapper of pygribjump.ExtractionRequest and the original FDB request dict.

    Can be removed once pygribjump.ExtractionRequest provides a reference to the request dictionary
    with original MARS keyword types.

    Parameters
    ----------
    extraction_request : pygj.ExtractionRequest
        The GribJump extraction request object.
    request : dict[str, str]
        The original request dictionary used to create the extraction request.
    """

    extraction_request: pygj.ExtractionRequest
    request: dict[str, Any]

    @property
    def ranges(self) -> list[tuple[int, int]]:
        """Returns the ranges of the extraction request."""
        return self.extraction_request.ranges

    def indices(self) -> np.ndarray:
        """Returns the indices of the extraction request."""
        return self.extraction_request.indices()


def build_extraction_request(
    request: dict[str, str],
    ranges: Optional[list[tuple[int, int]]] = None,
    mask: Optional[np.ndarray] = None,
    indices: Optional[np.ndarray] = None,
) -> ExtractionRequest:
    """
    Builds an ExtractionRequest from the given request dictionary and optional parameters.

    Parameters
    ----------
    request : dict[str, str]
        The request dictionary containing MARS keywords.
    ranges : Optional[list[tuple[int, int]]], optional
        The ranges for the extraction request, by default None.
    mask : Optional[np.ndarray], optional
        The mask for the extraction request, by default None.
    indices : Optional[np.ndarray], optional
        The indices for the extraction request, by default None.

    Returns
    -------
    ExtractionRequest
        The constructed ExtractionRequest object.
    """
    stringified_request_dict = {k: str(v) for (k, v) in request.items()}

    if sum(opt is not None for opt in (ranges, mask, indices)) != 1:
        raise ValueError(
            "Exactly one of 'ranges', 'mask' or 'indices' must be set. " f"Got {ranges=}, {mask=}, {indices=}"
        )

    if ranges is not None:
        extraction_request = pygj.ExtractionRequest(stringified_request_dict, ranges)
    elif mask is not None:
        extraction_request = pygj.ExtractionRequest.from_mask(stringified_request_dict, mask)
    elif indices is not None:
        extraction_request = pygj.ExtractionRequest.from_indices(stringified_request_dict, indices)
    else:
        raise ValueError("No valid extraction method specified. Provide either ranges, mask, or indices.")

    return ExtractionRequest(extraction_request, request)


class ExtractionRequestCollection(UserList):

    @classmethod
    def from_mars_requests(
        cls,
        mars_requests: list[dict[str, str]],
        ranges: Optional[list[tuple[int, int]]] = None,
        mask: Optional[np.ndarray] = None,
        indices: Optional[np.ndarray] = None,
    ) -> "ExtractionRequestCollection":
        """Creates an ExtractionRequestCollection from MARS requests.

        One of the parameters `ranges`, `mask`, or `indices` must be provided.

        Parameters
        ----------
        mars_requests : list[dict[str, str]]
            List of MARS requests, each represented as a dictionary of keywords.
        ranges : Optional[list[tuple[int, int]]], optional
            The ranges for the extraction requests, by default None.
        mask : Optional[np.ndarray], optional
            The mask for the extraction requests, by default None.
        indices : Optional[np.ndarray], optional
            The indices for the extraction requests, by default None.
        Returns
        -------
        ExtractionRequestCollection
            A collection of ExtractionRequest objects created from the MARS requests.
        """

        if sum(opt is not None for opt in (ranges, mask, indices)) != 1:
            raise ValueError(
                "Exactly one of 'ranges', 'mask' or 'indices' must be set. "
                f"Got {ranges=}, {mask=}, {indices=}"
            )

        if mask is not None:
            # Since PyGribJump converts the mask to ranges internally,
            # we convert it to ranges here once to avoid doing this multiple times.
            ranges = mask_to_ranges(mask)
            mask = None

        extraction_requests = [build_extraction_request(req, ranges, mask, indices) for req in mars_requests]
        return cls(extraction_requests)


class FieldExtractList(SimpleFieldList):
    """Lazily loaded representation of points extracted from multiple fields using GribJump.

    .. warning::
        This implementation is **not thread-safe**. Concurrent access from multiple threads
        may result in race conditions during lazy loading. Use appropriate synchronization
        if accessing from multiple threads.

    .. note::
        This class should not be instantiated directly. Use the ``gribjump`` source instead:
        ``earthkit.data.from_source("gribjump", request, ranges=ranges)``

    This class inherits from SimpleFieldList and provides lazy loading of grid point
    extractions from GRIB fields via GribJump. FieldList operations like ``sel()``,
    ``group_by()``, etc. might work but are not guaranteed to be fully functional.

    Known Limitations
    -----------------
    * **No validation**: Grid indices are not validated against actual field grids.
        Incorrect indices may return unexpected grid points.
    * **Not thread-safe**: Concurrent access may cause race conditions during lazy loading.
    * **Limited metadata**: Only metadata from the request dictionary is available,
        except for latitude/longitude coordinates when ``fetch_coords_from_fdb=True`` is used.
    * **No efficient slicing**: Lazy loading of selections/slices is not supported.
    * **Serialization issues**: Pickling/unpickling might not work reliably.
    """

    def __init__(
        self,
        gj: pygj.GribJump,
        requests: ExtractionRequestCollection,
        fdb_retriever: Optional[FDBRetriever] = None,
    ):
        self._gj = gj
        self._requests = requests
        self._fdb_retriever = fdb_retriever

        # These attributes are set lazily after loading the data.
        self._loaded = False
        self._grid_indices = None
        self._reference_metadata: Optional[GribMetadata] = None

        super().__init__(fields=None)

    def __len__(self):
        self._load()
        return super().__len__()

    def __getitem__(self, n):
        self._load()
        return super().__getitem__(n)

    def _load(self):
        if self._loaded:
            return

        extraction_requests = [req.extraction_request for req in self._requests]

        context = {"origin": "earthkit-data"}
        extraction_results = self._gj.extract(extraction_requests, ctx=context)

        fields = []
        indices = None
        ranges = None
        for request, result in zip(self._requests, extraction_results):
            if ranges is None:
                ranges = request.ranges
                indices = request.indices()
            else:
                if request.ranges != ranges:
                    raise ValueError(
                        f"Extraction request has different ranges than the first request: {request.ranges} != {ranges}"
                    )
            arr = result.values_flat
            shape = arr.shape

            metadata = UserMetadata(request.request, shape=shape)
            metadata = self._enrich_metadata_with_coordinates(indices, metadata)

            field = ArrayField(arr, metadata)
            fields.append(field)

        self.fields = fields
        self._loaded = True
        self._grid_indices = indices

    def _load_reference_metadata(self):
        """Loads the reference metadata from the FDB retriever if available."""
        if self._fdb_retriever is None:
            return None
        if self._reference_metadata is not None:
            return self._reference_metadata

        fields = self._fdb_retriever.get(self._requests[0].request)
        metadatas = fields.metadata()
        if not metadatas:
            raise ValueError("FDB retriever returned no metadata.")
        if len(metadatas) != 1:
            raise ValueError(f"Expected exactly one metadata for the first request, got {len(metadatas)}.")
        metadata = metadatas[0]
        assert isinstance(metadata, GribMetadata), type(metadata)
        self._reference_metadata = metadata
        return metadata

    def _enrich_metadata_with_coordinates(self, indices: np.ndarray, metadata: UserMetadata) -> UserMetadata:
        """Enriches the metadata with coordinates if reference metadata is available."""
        if (reference_metadata := self._load_reference_metadata()) is None:
            return metadata

        reference_geography = reference_metadata.geography
        grid_latitudes = reference_geography.latitudes()[indices]
        grid_longitudes = reference_geography.longitudes()[indices]
        metadata = metadata.override(
            {
                "latitudes": grid_latitudes,
                "longitudes": grid_longitudes,
            }
        )
        return metadata

    def to_xarray(self, *args, **kwargs):
        kwargs = kwargs.copy()

        flatten_values = kwargs.setdefault("flatten_values", True)
        rename_dims = kwargs.setdefault("rename_dims", {"values": "index"})
        if not flatten_values:
            raise ValueError(
                "GribJump source only supports flattening of values. "
                "Please skip the 'flatten_values' argument or set it to True."
            )
        if rename_dims.get("values") != "index":
            raise ValueError(
                "GribJump source does not support renaming 'values' dimension. "
                "Please remove 'values' from 'rename_dims' argument."
            )

        ds = super().to_xarray(*args, **kwargs)
        ds = ds.assign_coords({"index": self._grid_indices})
        return ds

    def to_pandas(self, *args, **kwargs):
        self._not_implemented()


class GribJumpSource(Source):
    """Source for extracting grid points from GRIB messages in an FDB with GribJump.

    ⚠️ This source is experimental and may change in future versions without
    warning. It performs no validation that the specified grid indices
    correspond to the fields' actual underlying grids. The provided ranges
    might, therefore, correspond to unexpected points on the grid. This source
    is also currently not thread-safe.
    """

    def __init__(
        self,
        request: dict,
        *,
        ranges: Optional[list[tuple[int, int]]] = None,
        mask: Optional[np.ndarray] = None,
        indices: Optional[np.ndarray] = None,
        fetch_coords_from_fdb: bool = False,
        fdb_kwargs: Optional[dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Parameters
        ----------
        request : dict
            The MARS request dictionary describing the fields to retrieve.
        ranges : Optional[list[tuple[int, int]]], optional
            The ranges of grid indices to retrieve, by default None.
        mask : Optional[np.ndarray], optional
            A 1D boolean mask specifying which grid points to retrieve, by default None.
        indices : Optional[np.ndarray], optional
            A 1D array of grid indices to retrieve, by default None.
        fetch_coords_from_fdb : bool, optional
            If set to True, loads the first field's metadata from the FDB to extract the coordinates
            at the specified indices.
        fdb_kwargs : Optional[dict[str, Any]], optional
            Only used when `fetch_coords_from_fdb=True`. A dict of
            keyword arguments passed to the `pyfdb.FDB` constructor. These arguments are only passed
            to the FDB when fetching coordinates and is not used by GribJump for the extraction itself.
        """

        super().__init__(**kwargs)

        if sum(opt is not None for opt in (ranges, mask, indices)) != 1:
            raise ValueError(
                "Exactly one of 'ranges', 'mask' or 'indices' must be set. "
                f"Got {ranges=}, {mask=}, {indices=}"
            )
        self._ranges = ranges
        self._mask = mask
        self._indices = indices

        self._check_env()
        self._gj = pygj.GribJump()

        self._coords_from_fdb = fetch_coords_from_fdb
        self._fdb_kwargs = fdb_kwargs if fdb_kwargs is not None else {}
        self._mars_requests = split_mars_requests(request)

    def _check_env(self):
        fdb_home = os.environ.get("FDB_HOME", None)
        fdb_config = os.environ.get("FDB5_CONFIG", None)
        fdb_config_file = os.environ.get("FDB5_CONFIG_FILE", None)

        gj_home = os.environ.get("GRIBJUMP_HOME", None)
        gj_config_file = os.environ.get("GRIBJUMP_CONFIG_FILE", None)
        gj_ignore_grid = os.environ.get("GRIBJUMP_IGNORE_GRID", None)

        if fdb_home is None and fdb_config is None and fdb_config_file is None:
            raise RuntimeError(
                """Neither FDB_HOME, FDB5_CONFIG, nor FDB5_CONFIG_FILE environment variable
                was set! Please define at least one to access FDB.
                See: https://fields-database.readthedocs.io for details about FDB."""
            )
        if gj_home is None and gj_config_file is None:
            raise RuntimeError(
                """Neither GRIBJUMP_HOME nor GRIBJUMP_CONFIG_FILE environment variable
                was set! Please define at least one to access GribJump.
                See: https://github.com/ecmwf/gribjump for details about GribJump."""
            )
        if gj_ignore_grid is None:
            # We could consider setting this automatically but this would need
            # to be done carefully to not accidentally activate this for other
            # gribjump accesses (e.g. through polytope).
            raise RuntimeError(
                "Environment variable 'GRIBJUMP_IGNORE_GRID' is not set but "
                "must be set (to '1' or 'True') for the 'gribjump' source to work."
            )

    def mutate(self):
        extraction_requests = ExtractionRequestCollection.from_mars_requests(
            self._mars_requests,
            ranges=self._ranges,
            mask=self._mask,
            indices=self._indices,
        )
        fdb_retriever = FDBRetriever(self._fdb_kwargs) if self._coords_from_fdb else None
        return FieldExtractList(
            self._gj,
            requests=extraction_requests,
            fdb_retriever=fdb_retriever,
        )


source = GribJumpSource
