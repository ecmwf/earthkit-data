# (C) Copyright 2024 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
from typing import Any
from typing import Dict
from typing import List

import xarray as xr

LOG = logging.getLogger(__name__)


def patch_attributes(ds: xr.Dataset, attributes: Dict[str, Dict[str, Any]]) -> Any:
    """Patch the attributes of the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset to patch.
    attributes : Dict[str, Dict[str, Any]]
        The attributes to patch.

    Returns
    -------
    Any
        The patched dataset.
    """
    for name, value in attributes.items():
        variable = ds[name]
        variable.attrs.update(value)

    return ds


def patch_coordinates(ds: xr.Dataset, coordinates: List[str]) -> Any:
    """Patch the coordinates of the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset to patch.
    coordinates : List[str]
        The coordinates to patch.

    Returns
    -------
    Any
        The patched dataset.
    """
    for name in coordinates:
        ds = ds.assign_coords({name: ds[name]})

    return ds


PATCHES = {
    "attributes": patch_attributes,
    "coordinates": patch_coordinates,
}


def patch_dataset(ds: xr.Dataset, patch: Dict[str, Dict[str, Any]]) -> Any:
    """Patch the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset to patch.
    patch : Dict[str, Dict[str, Any]]
        The patch to apply.

    Returns
    -------
    Any
        The patched dataset.
    """
    for what, values in patch.items():
        if what not in PATCHES:
            raise ValueError(f"Unknown patch type {what!r}")

        ds = PATCHES[what](ds, values)

    return ds
