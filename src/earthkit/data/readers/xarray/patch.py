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
from typing import Literal

import xarray as xr

LOG = logging.getLogger(__name__)


def patch_attributes(ds: xr.Dataset, attributes: dict[str, dict[str, Any]]) -> xr.Dataset:
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


def patch_coordinates(ds: xr.Dataset, coordinates: list[str]) -> xr.Dataset:
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


def patch_rename(ds: xr.Dataset, renames: dict[str, str]) -> xr.Dataset:
    """Rename variables in the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset to patch.
    renames : dict[str, str]
        Mapping from old variable names to new variable names.

    Returns
    -------
    Any
        The patched dataset.
    """
    return ds.rename(renames)


def patch_sort_coordinate(ds: xr.Dataset, sort_coordinates: list[str]) -> xr.Dataset:
    """Sort the coordinates of the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset to patch.
    sort_coordinates : List[str]
        The coordinates to sort.

    Returns
    -------
    Any
        The patched dataset.
    """

    for name in sort_coordinates:
        ds = ds.sortby(name)
    return ds


def patch_subset_dataset(ds: xr.Dataset, selection: dict[str, Any]) -> xr.Dataset:
    """Select a subset of the dataset using xarray's sel method.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset to patch.
    selection : dict[str, Any]
        Dictionary mapping dimension names to selection criteria.
        Keys must be existing dimension names in the dataset.
        Values can be any type accepted by xarray's sel method, including:
        - Single values (int, float, str, datetime)
        - Lists or arrays of values
        - Slices (using slice() objects)
        - Boolean arrays

    Returns
    -------
    xr.Dataset
        The patched dataset containing only the selected subset.

    Examples
    --------
    >>> # Select specific time and pressure level
    >>> patch_subset_dataset(ds, {"time": "2020-01-01", "pressure": 500})

    >>> # Select a range using slice
    >>> patch_subset_dataset(ds, {"lat": slice(-90, 90), "lon": slice(0, 180)})
    """

    ds = ds.sel(selection)

    return ds


def patch_analysis_lead_to_valid_time(
    ds: xr.Dataset,
    time_coord_names: dict[
        Literal["analysis_time_coordinate", "lead_time_coordinate", "valid_time_coordinate"], str
    ],
) -> xr.Dataset:
    """Convert analysis time and lead time coordinates to valid time.

    This function creates a new valid time coordinate by adding the analysis time
    and lead time coordinates, then stacks and reorganizes the dataset to use
    valid time as the primary time dimension.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset to patch.
    time_coord_names : dict[str, str]
        Dictionary mapping required keys to coordinate names in the dataset:

        - 'analysis_time_coordinate' : str
            Name of the analysis/initialization time coordinate.
        - 'lead_time_coordinate' : str
            Name of the forecast lead time coordinate.
        - 'valid_time_coordinate' : str
            Name for the new valid time coordinate to create.

    Returns
    -------
    xr.Dataset
        The patched dataset with valid time as the primary time coordinate.
        The analysis and lead time coordinates are removed.

    Examples
    --------
    >>> patch_analysis_lead_to_valid_time(
    ...     ds,
    ...     {
    ...         "analysis_time_coordinate": "forecast_reference_time",
    ...         "lead_time_coordinate": "step",
    ...         "valid_time_coordinate": "time",
    ...     },
    ... )
    """

    assert time_coord_names.keys() == {
        "analysis_time_coordinate",
        "lead_time_coordinate",
        "valid_time_coordinate",
    }, "time_coord_names must contain exactly keys 'analysis_time_coordinate', 'lead_time_coordinate', and 'valid_time_coordinate'"

    analysis_time_coordinate = time_coord_names["analysis_time_coordinate"]
    lead_time_coordinate = time_coord_names["lead_time_coordinate"]
    valid_time_coordinate = time_coord_names["valid_time_coordinate"]

    valid_time = ds[analysis_time_coordinate] + ds[lead_time_coordinate]

    ds = (
        ds.assign_coords({valid_time_coordinate: valid_time})
        .stack(time_index=[analysis_time_coordinate, lead_time_coordinate])
        .set_index(time_index=valid_time_coordinate)
        .rename(time_index=valid_time_coordinate)
        .drop_vars([analysis_time_coordinate, lead_time_coordinate])
    )

    return ds


def patch_rolling_operation(
    ds: xr.Dataset,
    vars_operation_config: dict[Literal["dim", "steps", "vars", "operation"], str | int | list[str]],
) -> xr.Dataset:
    """Apply a rolling operation to specified variables in the dataset.

    This function calculates a rolling operation over a specified dimension for selected
    variables. The rolling window requires all periods to be present (min_periods=steps).

    Parameters
    ----------
    ds : xr.Dataset
        The dataset to patch.
    vars_operation_config: dict
        Configuration for the rolling operation with the following keys:

        - 'dim' : str
            The dimension along which to apply the rolling operation (e.g., 'time').
        - 'steps' : int
            The number of steps in the rolling window.
        - 'vars' : list[str]
            List of variable names to apply the rolling operation to.
        - 'operation' : str
            The operation to apply ('sum', 'mean', 'min', 'max', 'std', etc.).

    Returns
    -------
    xr.Dataset
        The patched dataset with rolling operations applied to the specified variables.

    Examples
    --------
    >>> patch_rolling_operation(
    ...     ds,
    ...     {
    ...         "dim": "time",
    ...         "steps": 3,
    ...         "vars": ["precipitation", "radiation"],
    ...         "operation": "sum",
    ...     },
    ... )
    """

    assert vars_operation_config.keys() == {
        "dim",
        "steps",
        "vars",
        "operation",
    }, "vars_operation_config must contain exactly keys 'dim', 'steps', 'vars', and 'operation'"

    dim = vars_operation_config["dim"]
    steps = vars_operation_config["steps"]
    vars = vars_operation_config["vars"]
    operation = vars_operation_config["operation"]

    for var in vars:
        rolling = ds[var].rolling(dim={dim: steps}, min_periods=steps)
        ds[var] = getattr(rolling, operation)()

    return ds


PATCHES = {
    "attributes": patch_attributes,
    "coordinates": patch_coordinates,
    "rename": patch_rename,
    "sort_coordinates": patch_sort_coordinate,
    "analysis_lead_to_valid_time": patch_analysis_lead_to_valid_time,
    "rolling_operation": patch_rolling_operation,
    "subset_dataset": patch_subset_dataset,
}


def patch_dataset(ds: xr.Dataset, patch: dict[str, dict[str, Any]]) -> Any:
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

    ORDER = [
        "coordinates",
        "attributes",
        "rename",
        "sort_coordinates",
        "subset_dataset",
        "analysis_lead_to_valid_time",
        "rolling_operation",
    ]
    for what, values in sorted(patch.items(), key=lambda x: ORDER.index(x[0])):
        if what not in PATCHES:
            raise ValueError(f"Unknown patch type {what!r}")

        ds = PATCHES[what](ds, values)

    return ds
