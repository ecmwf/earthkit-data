# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import xarray as xr
import yaml

from earthkit.data.indexing.fieldlist import FieldList

# from .field import EmptyFieldList
from .flavour import CoordinateGuesser
from .patch import patch_dataset
from .time import Time
from .variable import FilteredVariable
from .variable import Variable

LOG = logging.getLogger(__name__)


class XArrayFieldList(FieldList):
    """A class to represent a list of fields from an xarray Dataset."""

    def __init__(self, ds: xr.Dataset, variables: List[Variable]) -> None:
        """Initialize the XarrayFieldList.

        Parameters
        ----------
        ds : xr.Dataset
            The xarray Dataset.
        variables : List[Variable]
            The list of variables.
        """
        self.ds: xr.Dataset = ds
        self.variables: List[Variable] = variables.copy()
        self.total_length: int = sum(v.length for v in variables)

        # LOG.debug(f"Created XArrayFieldList with {self.total_length} fields from {len(variables)} variables")

    def __repr__(self) -> str:
        """Return a string representation of the XarrayFieldList."""
        return f"XarrayFieldList({self.total_length})"

    def __len__(self) -> int:
        """Return the length of the XarrayFieldList."""
        return self.total_length

    def _getitem(self, n):
        if isinstance(n, int):
            # LOG.debug(f"Getting item {n} from XArrayFieldList")
            return self._getitem_core(n)

    def _getitem_core(self, i: int) -> Any:
        """Get an item from the XarrayFieldList by index.

        Parameters
        ----------
        i : int
            The index of the item to get.

        Returns
        -------
        Any
            The item at the specified index.

        Raises
        ------
        IndexError
            If the index is out of range.
        """
        k: int = i

        if i < 0:
            i = self.total_length + i

        for v in self.variables:
            if i < v.length:
                # LOG.debug(f"Selecting field {i} from variable {v.name}")
                return v[i]
            i -= v.length

        raise IndexError(k)

    @classmethod
    def from_xarray(
        cls,
        ds: xr.Dataset,
        *,
        flavour: Optional[Union[str, Dict[str, Any]]] = None,
        patch: Optional[Dict[str, Any]] = None,
    ):
        """Create an XarrayFieldList from an xarray Dataset.

        Parameters
        ----------
        ds : xr.Dataset
            The xarray Dataset to create the field list from.
        flavour : Optional[Union[str, Dict[str, Any]]], optional
            The flavour to use for guessing coordinates.
        patch : Optional[Dict[str, Any]], optional
            The patch to apply to the dataset.

        Returns
        -------
        XarrayFieldList
            The created XarrayFieldList.
        """
        if patch is not None:
            ds = patch_dataset(ds, patch)

        variables: List[Variable] = []

        if isinstance(flavour, str):
            with open(flavour) as f:
                if flavour.endswith(".yaml") or flavour.endswith(".yml"):
                    flavour = yaml.safe_load(f)
                else:
                    flavour = json.load(f)

        if isinstance(flavour, Dict):
            flavour_coords: List[str] = [coords["name"] for coords in flavour["rules"].values()]
            ds_dims: List[str] = [dim for dim in ds._dims]
            for dim in ds_dims:
                if dim in flavour_coords and dim not in ds._coord_names:
                    ds = ds.assign_coords({dim: ds[dim]})
                else:
                    pass

        guess = CoordinateGuesser.from_flavour(ds, flavour)

        skip: set = set()

        def _skip_attr(v: Any, attr_name: str) -> None:
            attr_val: str = getattr(v, attr_name, "")
            if isinstance(attr_val, str):
                skip.update(attr_val.split(" "))

        for name in ds.data_vars:
            variable = ds[name]
            _skip_attr(variable, "coordinates")
            _skip_attr(variable, "bounds")
            _skip_attr(variable, "grid_mapping")

        LOG.debug("Xarray data_vars: %s", ds.data_vars)

        # Select only geographical variables
        for name in ds.data_vars:

            if name in skip:
                continue

            variable = ds[name]
            coordinates: List[Any] = []

            for coord in variable.coords:

                c = guess.guess(ds[coord], coord)
                assert c, f"Could not guess coordinate for {coord}"
                if coord not in variable.dims:
                    LOG.debug("%s: coord=%s (not a dimension): dims=%s", variable, coord, variable.dims)
                    c.is_dim = False
                coordinates.append(c)

            grid_coords: int = sum(1 for c in coordinates if c.is_grid)
            # assert grid_coords <= 2, [c for c in coordinates if c.is_grid]

            if grid_coords < 2:
                LOG.debug(
                    "Skipping %s (not 2D): %s", variable, [(c, c.is_grid, c.is_dim) for c in coordinates]
                )
                continue

            v = Variable(
                ds=ds,
                variable=variable,
                coordinates=coordinates,
                grid=guess.grid(coordinates, variable),
                time=Time.from_coordinates(coordinates),
                metadata={},
            )

            variables.append(v)

        return cls(ds, variables)

    def sel(self, *args, **kwargs: Any) -> FieldList:
        """Select fields from the XarrayFieldList based on criteria.

        Parameters
        ----------
        kwargs : dict
            The selection criteria.

        Returns
        -------
        FieldList
            The new FieldList with selected fields.
        """

        """
        The algorithm is as follows:
        1 - Use the kwargs to select the variables that match the selection (`param` or `variable`)
        2 - For each variable, use the remaining kwargs to select the coordinates (`level`, `number`, ...)
        3 - Some mars like keys, like `date`, `time`, `step` are not found in the coordinates,
            but added to the metadata of the selected fields. A example is `step` that is added to the
            metadata of the field. Step 2 may return a variable that contain all the fields that
            verify at the same `valid_datetime`, with different base `date` and `time` and a different `step`.
            So we get an extra chance to filter the fields by the metadata.
        """
        from earthkit.data.core.select import normalize_selection

        kwargs = normalize_selection(*args, **kwargs)
        if not kwargs:
            return self

        if hasattr(self, "normalise_key_values"):
            kwargs = self.normalise_key_values(**kwargs)

        variables: List[Variable] = []
        count: int = 0

        for v in self.variables:

            # First, select matching variables

            # This will consume 'param' or 'variable' from kwargs
            # and return the rest
            match, rest = v.match(**kwargs)

            if match:
                count += 1
                missing: Dict[str, Any] = {}

                # Select from the variable's coordinates (time, level, number, ....)
                # This may return a new variable with a isel() slice of the selection
                # or None if the selection is not possible. In this case, missing is updated
                # with the values of kwargs (rest) that are not relevant for this variable
                v = v.sel(missing, **rest)
                if missing:
                    if v is not None:
                        # The remaining kwargs are passed used to create a FilteredVariable
                        # that will select 2D slices based on their metadata
                        v = FilteredVariable(v, **missing)
                    else:
                        LOG.warning(f"Variable {v} has missing coordinates: {missing}")

                if v is not None:
                    variables.append(v)

        if count == 0:
            LOG.warning("No variable found for %s", kwargs)
            LOG.warning("Variables: %s", sorted([v.name for v in self.variables]))

        if not variables:
            from earthkit.data.indexing.empty import EmptyFieldList

            return EmptyFieldList()

        # return self.__class__(self.ds, variables)
        return XArrayFieldList(self.ds, variables)

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        assert len(args) == 2
        fl = args[0]
        indices = list(args[1])
        return cls.from_fields([fl[i] for i in indices])
