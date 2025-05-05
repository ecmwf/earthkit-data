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

import numpy as np

from earthkit.data.sources import Source


def expand_multivalued_dicts(
    request: dict[str, str | list[str]],
) -> list[dict[str, str]]:
    """
    Expands a dictionary with list values into multiple dictionaries,
    each containing one combination of the list values.

    Example:
        Input: {'a': [1, 2], 'b': [3, 4], 'c': 5}
        Output: [{'a': 1, 'b': 3, 'c': 5}, {'a': 1, 'b': 4, 'c': 5},
                 {'a': 2, 'b': 3, 'c': 5}, {'a': 2, 'b': 4, 'c': 5}]

    Args:
        request (dict): The original dictionary containing keys and values.

    Returns:
        list: A list of dictionaries, each representing a unique combination
              of the list values in the original dictionary.
    """
    list_keywords = [k for k, v in request.items() if isinstance(v, list)]
    values = [request[k] for k in list_keywords]
    expanded_requests = []
    for combination in itertools.product(*values):
        new_request = request.copy()
        for k, v in zip(list_keywords, combination):
            new_request[k] = v
        expanded_requests.append(new_request)
    return expanded_requests


class GribJumpSource(Source):
    def __init__(
        self,
        request: dict,
        *,
        ranges: list[tuple[int, int]] | None = None,
        mask: np.ndarray | None = None,
        indices: np.ndarray | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if sum(opt is not None for opt in (ranges, mask, indices)) != 1:
            raise ValueError(
                "Exactly one of 'ranges', 'mask' or 'indices' must be set. "
                f"Got {ranges=}, {mask=}, {indices=}"
            )
        self._ranges = ranges
        self._masks = mask
        self._indices = indices

        self._check_env()
        self._gj = pygj.GribJump()
        self._requests = self._split_mars_requests(request)

    def _check_env(self):
        gj_config_file = os.environ.get("GRIBJUMP_CONFIG_FILE", None)
        gj_ignore_grid = os.environ.get("GRIBJUMP_IGNORE_GRID", None)

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
        Additionally performs some basic validation and converts all values to strings.
        """

        request = request.copy()

        # Check for invalid values and cast anything but lists to strings
        for k in request.keys():
            v = request[k]
            if isinstance(v, str) and "/" in v:
                # TODO: Check if there are valid reasons to use '/' apart from
                # lists and ranges.
                raise ValueError(
                    f"Found unexpected '/' in value '{v}' for keyword '{k}'. "
                    "Use Python lists to load from multiple fields."
                )
            elif not isinstance(v, list):
                request[k] = str(v)
            else:
                request[k] = [str(i) for i in v]

        # Expand the request into all combinations of the list values
        expanded_requests = expand_multivalued_dicts(request)
        return expanded_requests

    def _build_extraction_requests(self) -> list[pygj.ExtractionRequest]:
        if self._ranges is not None:
            requests = [pygj.ExtractionRequest(request, self._ranges) for request in self._requests]
        elif self._masks is not None:
            requests = [pygj.ExtractionRequest.from_mask(request, self._masks) for request in self._requests]
        elif self._indices is not None:
            requests = [
                pygj.ExtractionRequest.from_indices(request, self._indices) for request in self._requests
            ]
        else:
            raise ValueError(
                "No valid extraction request found. " "Please set either 'ranges', 'mask' or 'indices'."
            )
        return requests

    def to_numpy(self, **kwargs):
        extract_iter = self._gj.extract(self._build_extraction_requests())
        flattened_arrays = [res.values_flat for res in extract_iter]
        combined_array = np.stack(flattened_arrays)
        return combined_array


source = GribJumpSource
