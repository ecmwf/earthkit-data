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

import itertools
import os
from typing import Any
from typing import Optional
from typing import Union

import numpy as np

from earthkit.data.indexing.fieldlist import SimpleFieldList
from earthkit.data.sources import Source
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
    * FieldExtractList.sel is quite brittle as any filter value must be a string.
     The underlying metadata is stored as a dictionary of strings, and no
     automatic type conversion is done. Any more complex filtering and slicing
     will not work for most data types. Also, order_by and similar methods will
     perform lexicographical sorting on the string values.
    * Efficient lazy loading of selections / slices only is not supported.
    * Pickling / unpickling might not work.
    * to_pandas and to_xarray methods are not implemented.
    """

    def __init__(
        self,
        gj: pygj.GribJump,
        requests: list[dict[str, str]],
        extraction_requests: list[pygj.ExtractionRequest],
    ):
        if len(requests) != len(extraction_requests):
            raise ValueError(
                f"Number of MARS requests ({len(requests)}) and GribJump extraction requests ({len(extraction_requests)}) must match."
            )
        self._gj = gj
        self._requests = requests
        self._extraction_requests = extraction_requests
        self._loaded = False

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

        extraction_results = self._gj.extract(self._extraction_requests)

        fields = []
        for i, result in enumerate(extraction_results):
            arr = result.values_flat
            metadata = self._requests[i]
            field = ArrayField(arr, UserMetadata(metadata, shape=arr.shape))
            fields.append(field)

        self.fields = fields
        self._loaded = True

    def to_xarray(self, *args, **kwargs):
        self._not_implemented()

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
        **kwargs,
    ):
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

        self._mars_requests = self._split_mars_requests(request)
        self._gj_extraction_requests = self._build_extraction_requests(self._mars_requests)

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
        Additionally performs some basic validation and converts all values to strings since
        GribJump only supports string values in the request.
        """

        request = request.copy()

        # Check for invalid values and cast anything but lists to strings
        for k in request.keys():
            v = request[k]
            if isinstance(v, str) and "/" in v:
                # TODO: Check if there are valid reasons to use '/' apart from
                # lists and ranges.
                raise ValueError(
                    f"Found unsupported list or range using '/' in value '{v}' for keyword '{k}'. "
                    "Use Python lists to load from multiple fields."
                )
            elif not isinstance(v, list):
                request[k] = str(v)
            else:
                request[k] = [str(i) for i in v]

        expanded_requests = expand_dict_with_lists(request)
        return expanded_requests

    def _build_extraction_requests(self, mars_requests: list[dict[str, str]]) -> list[pygj.ExtractionRequest]:
        if self._ranges is not None:
            requests = [pygj.ExtractionRequest(request, self._ranges) for request in mars_requests]
        elif self._mask is not None:
            requests = [pygj.ExtractionRequest.from_mask(request, self._mask) for request in mars_requests]
        elif self._indices is not None:
            requests = [
                pygj.ExtractionRequest.from_indices(request, self._indices) for request in mars_requests
            ]
        else:
            raise ValueError("No valid extraction method specified.")
        return requests

    def mutate(self):
        return FieldExtractList(
            self._gj,
            self._mars_requests,
            self._gj_extraction_requests,
        )


source = GribJumpSource
