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

from earthkit.data.core.gridspec import GridSpec
from earthkit.data.indexing.fieldlist import SimpleFieldList
from earthkit.data.readers.grib.metadata import GribMetadata
from earthkit.data.sources import Source
from earthkit.data.sources.array_list import ArrayField
from earthkit.data.sources.fdb import FDBRetriever
from earthkit.data.utils.metadata.dict import UserMetadata


def split_mars_requests(request: dict[str, Any]) -> list[dict[str, str]]:
    """Splits a MARS request into individual single-field requests by expanding list values.

    Creates all possible combinations of list values in the request dictionary,
    generating separate requests for each field. This is required because GribJump
    returns result arrays without metadata, so each field must be requested individually
    to map outputs correctly.

    Parameters
    ----------
    request : dict[str, Any]
        The request dictionary containing MARS keywords with potentially list values.
        List keys are sorted alphabetically to ensure deterministic ordering.

    Returns
    -------
    list[dict[str, str]]
        A list of individual request dictionaries, each representing a single field.
        All values are converted to strings.

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
    [{'param': '2t', 'step': '0'}, {'param': '2t', 'step': '6'},
     {'param': 'msl', 'step': '0'}, {'param': 'msl', 'step': '6'}]
    """
    request = request.copy()

    # Validation
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


def verify_gridspec(expected: dict, actual: GridSpec) -> None:
    actual = dict(actual)
    for key, value in expected.items():
        if key not in actual:
            raise ValueError(f"Gridspec mismatch for key '{key}': expected {value}, got None")
        if isinstance(value, (list, np.ndarray)):
            if not np.array_equal(value, actual[key]):
                raise ValueError(f"Gridspec mismatch for key '{key}': expected {value}, got {actual[key]}")
        else:
            if value != actual[key]:
                raise ValueError(f"Gridspec mismatch for key '{key}': expected {value}, got {actual[key]}")


@dataclasses.dataclass
class ExtractionRequest:
    """
    Simple wrapper of pygribjump.ExtractionRequest and the original FDB request dict.

    Can be removed once pygribjump.ExtractionRequest provides a reference to the request dictionary.

    Parameters
    ----------
    extraction_request : pygj.ExtractionRequest
        The GribJump extraction request object.
    request : dict[str, str]
        The original request dictionary used to create the extraction request.
    """

    extraction_request: pygj.ExtractionRequest
    request: dict[str, str]

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
        if not isinstance(mask, np.ndarray):
            raise TypeError(f"Expected 'mask' to be a numpy array, got {type(mask)}")
        if not np.issubdtype(mask.dtype, np.bool_):
            raise ValueError(f"Expected 'mask' to be a boolean array, got {mask.dtype}")
        if mask.ndim != 1:
            raise ValueError(f"Expected 'mask' to be a 1D numpy array, got {mask.ndim}D")
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
        extraction_requests = [build_extraction_request(req, ranges, mask, indices) for req in mars_requests]
        return cls(extraction_requests)


class FieldExtractList(SimpleFieldList):
    """Lazily loaded representation of the points extracted from multiple fields using GribJump.

    For simplicity, this class currently inherits from SimpleFieldList and is
    inspired by the FieldlistFromDicts and GribFieldListInMemory classes.
    However, it is not a complete implementation and can break in unexpected
    ways. The main reason for this is that although the arrays with the
    extracted values are represented as ArrayFields, they are not truly proper
    Field implementations. They are neither stored as 2D grids, nor do they
    possess any geographical information or well-defined metadata.

    Known limitations:
    * FieldExtractList.sel is quite brittle as any filter values must have the same type
      as the metadata in the user's request dictionary. The actual type of the underlying
      MARS keyword is not respected. So ".sel(step=0) would not work with a request
      {"step": "0"} but only {"step": 0}.
    * Efficient lazy loading of selections / slices only is not supported.
    * Pickling / unpickling might not work.
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

        self._loaded = False
        self._grid_indices = None
        self._reference_metadata: Optional[GribMetadata] = None

        super().__init__(fields=None)  # The fields attribute is set lazily

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
        extraction_results = self._gj.extract(extraction_requests)

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
    def __init__(
        self,
        request: dict,
        *,
        ranges: Optional[list[tuple[int, int]]] = None,
        mask: Optional[np.ndarray] = None,
        indices: Optional[np.ndarray] = None,
        coords_from_fdb: bool = False,
        verify_gridspec: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if sum(opt is not None for opt in (ranges, mask, indices)) != 1:
            raise ValueError(
                "Exactly one of 'ranges', 'mask' or 'indices' must be set. "
                f"Got {ranges=}, {mask=}, {indices=}"
            )
        if verify_gridspec is not None and not coords_from_fdb:
            raise ValueError(
                "If 'verify_gridspec' is set, 'coords_from_fdb' must also be set to True. "
                f"Got {coords_from_fdb=}, {verify_gridspec=}"
            )
        self._ranges = ranges
        self._mask = mask
        self._indices = indices

        self._check_env()
        self._gj = pygj.GribJump()

        self._coords_from_fdb = coords_from_fdb
        self._verify_gridspec = verify_gridspec
        self._mars_requests = split_mars_requests(request)

    def _check_env(self):
        fdb_conf = os.environ.get("FDB5_CONFIG", None)
        fdb_home = os.environ.get("FDB_HOME", None)
        gj_config_file = os.environ.get("GRIBJUMP_CONFIG_FILE", None)
        gj_ignore_grid = os.environ.get("GRIBJUMP_IGNORE_GRID", None)

        if fdb_home is None and fdb_conf is None:
            raise RuntimeError(
                """Neither FDB_HOME nor FDB5_CONFIG environment variable
                was set! Please define either one to access FDB.
                See: https://fields-database.readthedocs.io for details about FDB."""
            )
        if gj_config_file is None:
            raise RuntimeError(
                "Environment variable 'GRIBJUMP_CONFIG_FILE' is not set but "
                "is required by GribJump. Please set it to the path of the GribJump "
                "configuration file."
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
        # TODO: Allow proper configuration of the FDB retriever
        fdb_retriever = FDBRetriever({}) if self._coords_from_fdb else None

        extraction_requests = ExtractionRequestCollection.from_mars_requests(
            self._mars_requests,
            ranges=self._ranges,
            mask=self._mask,
            indices=self._indices,
        )

        return FieldExtractList(
            self._gj,
            requests=extraction_requests,
            fdb_retriever=fdb_retriever,
        )


source = GribJumpSource
