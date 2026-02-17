# (C) Copyright 2024 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
import math
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import numpy as np
import xarray as xr

from earthkit.data.decorators import thread_safe_cached_property

# from .field import XArrayField

LOG = logging.getLogger(__name__)


class Variable:
    """Represents a variable in an xarray dataset.

    Attributes
    ----------
    ds : xr.Dataset
        The xarray dataset.
    variable : xr.DataArray
        The data array representing the variable.
    coordinates : List[Any]
        List of coordinates associated with the variable.
    grid : Any
        The grid associated with the variable.
    time : Any
        The time dimension associated with the variable.
    metadata : Dict[str, Any]
        Metadata associated with the variable.
    """

    def __init__(
        self,
        *,
        ds: xr.Dataset,
        variable: xr.DataArray,
        coordinates: List[Any],
        grid: Any,
        time: Any,
        metadata: Dict[str, Any],
    ):
        """Initialize the Variable object.

        Parameters
        ----------
        ds : xr.Dataset
            The xarray dataset.
        variable : xr.DataArray
            The data array representing the variable.
        coordinates : List[Any]
            List of coordinates associated with the variable.
        grid : Any
            The grid associated with the variable.
        time : Any
            The time dimension associated with the variable.
        metadata : Dict[str, Any]
            Metadata associated with the variable.
        """
        self.ds = ds
        self.variable = variable

        self.grid = grid
        self.coordinates = coordinates

        self._metadata = metadata.copy()
        self._metadata.update({"variable": variable.name, "param": variable.name})

        self.time = time

        self.shape = tuple(
            len(c.variable) for c in coordinates if c.is_dim and not c.scalar and not c.is_grid
        )
        self.names = {c.variable.name: c for c in coordinates if c.is_dim and not c.scalar and not c.is_grid}
        self.by_name = {c.variable.name: c for c in coordinates}

        # We need that alias for the time dimension
        self._aliases = dict(valid_datetime="time")

        self.length = math.prod(self.shape)

    @property
    def name(self) -> str:
        """Return the name of the variable."""
        return str(self.variable.name)

    def __len__(self) -> int:
        """Return the length of the variable.

        Returns
        -------
        int
            The length of the variable.
        """
        return self.length

    # @property
    # def grid_mapping(self) -> Optional[Dict[str, Any]]:
    #     """Return the grid mapping of the variable."""
    #     grid_mapping = self.variable.attrs.get("grid_mapping", None)
    #     if grid_mapping is None:
    #         return None
    #     return self.ds[grid_mapping].attrs

    # def grid_points(self) -> Any:
    #     """Return the grid points of the variable.

    #     Returns
    #     -------
    #     Any
    #         The grid points of the variable.
    #     """
    #     return self.grid.grid_points

    # @property
    # def latitudes(self) -> Any:
    #     """Return the latitudes of the variable."""
    #     return self.grid.latitudes

    # @property
    # def longitudes(self) -> Any:
    #     """Return the longitudes of the variable."""
    #     return self.grid.longitudes

    def __repr__(self) -> str:
        """Return a string representation of the variable.

        Returns
        -------
        str
            A string representation of the variable.
        """
        return "Variable[name=%s,coordinates=%s,metadata=%s]" % (
            self.variable.name,
            self.coordinates,
            self._metadata,
        )

    def __getitem__(self, i: int):
        """Get a 2D field from the variable.

        Parameters
        ----------
        i : int
            Index of the field.

        Returns
        -------
        XArrayField
            The 2D field at the specified index.

        Raises
        ------
        IndexError
            If the index is out of range.
        """
        if i >= self.length:
            raise IndexError(i)

        coords = np.unravel_index(i, self.shape)
        kwargs = {k: v for k, v in zip(self.names, coords)}
        from earthkit.data.field.xarray.create import new_xarray_field

        LOG.debug(f"Creating field {i} from variable {self.name}")

        return new_xarray_field(self, self.variable.isel(kwargs))

    def sel(self, missing: Dict[str, Any], **kwargs: Any) -> Optional["Variable"]:
        """Select a subset of the variable based on the given coordinates.

        Parameters
        ----------
        missing : Dict[str, Any]
            Dictionary to store missing coordinates.
        **kwargs : Any
            Coordinates to select.

        Returns
        -------
        Optional[Variable]
            The selected subset of the variable.
        """
        if not kwargs:
            return self

        k, v = kwargs.popitem()

        user_provided_k = k

        if k == "time.valid_datetime":
            # Ask the Time object to select the valid datetime
            k = self.time.select_valid_datetime(self)
            if k is None:
                return None

        c = self.by_name.get(k)

        # assert c is not None, f"Could not find coordinate {k} in {self.variable.name} {self.coordinates} {list(self.by_name)}"

        if c is None:
            missing[k] = v
            return self.sel(missing, **kwargs)

        i = c.index(v)
        if i is None:
            if k != user_provided_k:
                LOG.warning(f"Could not find {user_provided_k}={v} in {c} (alias of {k})")
            else:
                LOG.warning(f"Could not find {k}={v} in {c}")
            return None

        coordinates = [x.reduced(i) if c is x else x for x in self.coordinates]

        metadata = self._metadata.copy()
        metadata.update({k: v})

        variable = Variable(
            ds=self.ds,
            variable=self.variable.isel({k: i}),
            coordinates=coordinates,
            grid=self.grid,
            time=self.time,
            metadata=metadata,
        )

        return variable.sel(missing, **kwargs)

    def match(self, **kwargs: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Match the variable based on the given metadata.

        Parameters
        ----------
        **kwargs : Any
            Metadata to match.

        Returns
        -------
        Tuple[bool, Optional[Dict[str, Any]]]
            A tuple containing a boolean indicating if the match was successful and the remaining metadata.
        """
        name = None
        if "parameter.variable" in kwargs:
            name = kwargs.pop("parameter.variable")

        if name is not None:
            if not isinstance(name, (list, tuple)):
                name = [name]
            if self.variable.name not in name:
                return False, None
            return True, kwargs

        return True, kwargs

        # if "param" in kwargs:
        #     assert "variable" not in kwargs
        #     kwargs["variable"] = kwargs.pop("param")

        # if "variable" in kwargs:
        #     name = kwargs.pop("variable")
        #     if not isinstance(name, (list, tuple)):
        #         name = [name]
        #     if self.variable.name not in name:
        #         return False, None
        #     return True, kwargs
        # return True, kwargs


class FilteredVariable:
    """Represents a filtered variable based on metadata.

    Attributes
    ----------
    variable : Variable
        The variable to filter.
    kwargs : Any
        Metadata to filter the variable.
    """

    def __init__(self, variable: Variable, **kwargs: Any):
        """Initialize the FilteredVariable object.

        Parameters
        ----------
        variable : Variable
            The variable to filter.
        **kwargs : Any
            Metadata to filter the variable.
        """
        self.variable = variable
        self.kwargs = kwargs

    @thread_safe_cached_property
    def fields(self):
        """Filter the fields of a variable based on metadata."""
        return [
            field
            for field in self.variable
            if all(field.get(k, default=None) == v for k, v in self.kwargs.items())
        ]

    @property
    def length(self) -> int:
        """Return the length of the filtered variable."""
        return len(self.fields)

    def __len__(self) -> int:
        """Return the length of the filtered variable.

        Returns
        -------
        int
            The length of the filtered variable.
        """
        return self.length

    def __getitem__(self, i: int):
        """Get a field from the filtered variable.

        Parameters
        ----------
        i : int
            Index of the field.

        Returns
        -------
        XArrayField
            The field at the specified index.

        Raises
        ------
        IndexError
            If the index is out of range.
        """
        if i >= self.length:
            raise IndexError(i)
        return self.fields[i]
