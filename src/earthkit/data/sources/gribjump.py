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
from typing import Any
from typing import Optional
from typing import Union

import numpy as np

from earthkit.data.core.gridspec import GridSpec
from earthkit.data.indexing.fieldlist import SimpleFieldList
from earthkit.data.readers.grib.metadata import GribMetadata
from earthkit.data.sources import Source
from earthkit.data.sources import from_source
from earthkit.data.sources.array_list import ArrayField
from earthkit.data.utils.metadata.dict import UserMetadata


def expand_dict_with_lists(
    request: dict[str, Union[str, list[str]]],
) -> list[dict[str, str]]:
    """
    Expands a dictionary containing list values into multiple dictionaries representing all possible combinations.

    For each list-type value in the input dictionary, this function creates all possible combinations
    with other list values, while keeping non-list values constant across all output dictionaries.

    The list keys are sorted alphabetically before generating combinations to ensure consistent
    and deterministic ordering of the output dictionaries regardless of the original key order.

    Example:
        Input: {'a': [1, 2], 'b': [3, 4], 'c': 5}
        Output: [
            {'a': 1, 'b': 3, 'c': 5},
            {'a': 1, 'b': 4, 'c': 5},
            {'a': 2, 'b': 3, 'c': 5},
            {'a': 2, 'b': 4, 'c': 5}
        ]

    Args:
        request (dict[str, Union[str, list[str]]]): Dictionary with string keys and either string
            or list of strings as values.

    Returns:
        list[dict[str, str]]: A list of dictionaries, where each dictionary contains one
            specific combination of the input list values, with non-list values preserved.
    """
    if empty_list_keys := [k for k, v in request.items() if isinstance(v, list) and len(v) == 0]:
        raise ValueError(
            "Cannot expand dictionary with empty list. "
            f"Found empty list for keys: {', '.join(empty_list_keys)}"
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
        requests: list[ExtractionRequest],
        reference_metadata: Optional[GribMetadata] = None,
    ):
        self._gj = gj
        self._requests = requests
        self._reference_metadata = reference_metadata

        self._loaded = False
        self._grid_indices = None

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
        geography = {}

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

            if self._reference_metadata is not None and not geography:
                reference_geography = self._reference_metadata.geography
                grid_latitudes = reference_geography.latitudes()[indices]
                grid_longitudes = reference_geography.longitudes()[indices]
                geography = {
                    "latitudes": grid_latitudes,
                    "longitudes": grid_longitudes,
                }

            metadata = UserMetadata(
                {
                    **geography,
                    **request.request,
                },
                shape=arr.shape,
            )

            field = ArrayField(arr, metadata)
            fields.append(field)

        self.fields = fields
        self._loaded = True
        self._grid_indices = indices

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
        self._mars_requests = self._split_mars_requests(request)
        self._extraction_requests = self._build_extraction_requests(self._mars_requests)

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

    @staticmethod
    def _split_mars_requests(request: dict[str, Any]) -> list[dict[str, str]]:
        """Splits request into many single requests that load one field each.

        Since GribJump returns its result arrays without metadata, we need to split the
        request into many single requests to later map the outputs to the correct fields.
        Additionally performs some basic validation.
        """

        request = request.copy()

        # Check if user passed unspoorted lists and ranges as strings using "/"
        for k in request.keys():
            v = request[k]
            if isinstance(v, str) and "/" in v:
                raise ValueError(
                    f"Found unsupported list or range using '/' in value '{v}' for keyword '{k}'. "
                    "Use Python lists to load from multiple fields."
                )
            elif isinstance(v, list) and len({type(v_) for v_ in v}) != 1:
                raise TypeError(
                    f"All list values must share the same type but found types {set(map(type, v))} "
                    f"in {k}={v}"
                )

        expanded_requests = expand_dict_with_lists(request)
        return expanded_requests

    def _build_extraction_request(self, request: dict[str, str]) -> ExtractionRequest:
        """Builds a single extraction request from the given request dictionary."""
        # GribJump currently only supports strings as request values
        stringified_request_dict = {k: str(v) for (k, v) in request.items()}

        if self._ranges is not None:
            extraction_request = pygj.ExtractionRequest(stringified_request_dict, self._ranges)
        elif self._mask is not None:
            extraction_request = pygj.ExtractionRequest.from_mask(stringified_request_dict, self._mask)
        elif self._indices is not None:
            extraction_request = pygj.ExtractionRequest.from_indices(stringified_request_dict, self._indices)
        else:
            raise ValueError("No valid extraction method specified.")
        return ExtractionRequest(extraction_request, request)

    def _build_extraction_requests(self, mars_requests: list[dict[str, str]]) -> list[ExtractionRequest]:
        """Builds extraction requests from the given MARS requests."""
        extraction_requests = [self._build_extraction_request(request) for request in mars_requests]
        return extraction_requests

    def mutate(self):
        # TODO: Find a more elegant way to load the reference metadata lazily
        # and in the right place.
        reference_metadata: GribMetadata | None = None
        if self._coords_from_fdb:
            fdb_source = from_source("fdb", self._mars_requests[0], stream=False)
            fdb_metadatas = fdb_source.metadata()
            if not fdb_metadatas:
                # TODO: This should be handled more gracefully
                raise ValueError("FDB source returned no metadata.")
            reference_metadata = fdb_metadatas[0]
            verify_gridspec(
                self._verify_gridspec or {},
                reference_metadata.gridspec,
            )

        return FieldExtractList(
            self._gj,
            self._extraction_requests,
            reference_metadata=reference_metadata,
        )


source = GribJumpSource
