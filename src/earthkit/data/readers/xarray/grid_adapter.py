# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""earthkit-data view of the grids computed by earthkit-geo.

:mod:`earthkit.geo.grids.xarray` builds the geography of an ``xarray``
variable (see its :class:`~earthkit.geo.grids.xarray.XarrayGrid`): the flat
``latlons`` and ``xys`` point arrays are exactly what the earthkit-data xarray
fields need, so they are used as they are. Three details of the interface are
earthkit-data's own and are pinned here:

- :attr:`bbox` returns a
  :class:`BoundingBox <earthkit.data.utils.bbox.BoundingBox>` instead of the
  ``(north, south, east, west)`` tuple earthkit-geo returns,
- :attr:`projection` returns a
  :class:`Projection <earthkit.data.utils.projections.Projection>` built from
  the CF grid mapping of the variable,
- :attr:`grid_type` is the eckit-geo grid type of the lat/lon grid, or ``None``
  for a grid that only has projected or plain x/y coordinates, whatever
  eckit-geo type earthkit-geo detects for it.
"""

import logging
from typing import Any, Optional

from earthkit.geo.grids.xarray import ProjectionGrid
from earthkit.geo.grids.xarray import XarrayGrid as GeoXarrayGrid

from earthkit.data.utils.bbox import BoundingBox

LOG = logging.getLogger(__name__)


class XarrayGrid(GeoXarrayGrid):
    """Grid class for the xarray readers, adding the earthkit-data interface to an earthkit-geo grid.

    Parameters
    ----------
    latlon_grid : LatLonGrid, optional
        The variable's lat/lon grid, if available.
    xy_grid : XYGrid, optional
        The variable's x/y grid, if available.
    """

    @property
    def bbox(self) -> BoundingBox:
        """BoundingBox: The bounding box of the grid, from its lat/lon points."""
        # earthkit-geo returns (north, south, east, west)
        north, south, east, west = super().bbox
        return BoundingBox(north=north, south=south, east=east, west=west)

    @property
    def projection(self) -> Optional[Any]:
        """Projection or None: The projection of the grid, from its x/y grid grid mapping."""
        if isinstance(self.xy_grid, ProjectionGrid):
            from earthkit.data.utils.projections import Projection

            return Projection.from_cf_grid_mapping(**self.xy_grid.projection)

        return None

    @property
    def grid_type(self) -> Optional[str]:
        """Str or None: The eckit-geo grid type, only for grids with latitude and longitude coordinates."""
        if self.latlon_grid is not None:
            return self.latlon_grid.grid_type

        return None
