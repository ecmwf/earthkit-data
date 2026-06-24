.. _geography_component:

Geography component
===================

Every :py:class:`~earthkit.data.core.field.Field` carries a *geography component* that describes
the horizontal spatial coordinate system of the field. The geography component is accessible via
the :attr:`geography` attribute of a field and is represented by a subclass of
:py:class:`~earthkit.data.field.component.geography.GeographyBase`.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> field = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
    >>> field.geography.shape
    (19, 36)
    >>> field.geography.area()
    (70, -20, 35, 40)
    >>> field.geography.grid_type()
    'regular_ll'

The same information is available through the generic :meth:`~earthkit.data.core.field.Field.get`
interface using the ``"geography."`` prefix:

.. code-block:: python

    >>> field.get("geography.area")
    (70, -20, 35, 40)
    >>> field.get("geography.shape")
    (19, 36)

The geography component is **immutable**. Use the
:meth:`~earthkit.data.field.component.geography.GeographyBase.set` method (or
:meth:`~earthkit.data.core.field.Field.set` on the field) to derive a modified copy.
When changing the grid it is typically necessary to supply new field values to match the
new grid shape:

.. code-block:: python

    >>> import numpy as np
    >>> values = np.random.rand(19, 36)
    >>> new_field = field.set({"geography.grid_spec": [10, 10], "values": values})
    >>> new_field.geography.area()
    (90.0, 0, -90.0, 360.0)


Geography types
---------------

The appropriate geography subclass is determined automatically from the data:

- **LatLonGeography** — irregular or curvilinear lat/lon grid where every point has an
  explicit latitude and longitude.
- **MeshedLatLonGeography** — regular lat/lon grid defined by distinct (1-D) latitude and
  longitude arrays that form a full Cartesian mesh.
- **GridsSpecBasedGeography** — grid defined by an eckit-geo grid specification string or
  dictionary (requires optional eckit-geo grid support).
- **EmptyGeography** — placeholder used when no coordinate information is available.


Accessing geography information
--------------------------------

All geography keys are accessible through :meth:`~earthkit.data.core.field.Field.get` with the
``"geography."`` prefix, and can therefore be used in
:meth:`~earthkit.data.core.fieldlist.FieldList.sel`,
:meth:`~earthkit.data.core.fieldlist.FieldList.order_by`, and
:meth:`~earthkit.data.core.fieldlist.FieldList.metadata`.

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Key
     - Description
   * - ``geography.latitudes``
     - Array of latitude values for every grid point. ``dtype`` argument supported for type control.
   * - ``geography.longitudes``
     - Array of longitude values for every grid point. ``dtype`` argument supported for type control.
   * - ``geography.distinct_latitudes``
     - 1-D array of unique latitude values for regular grids, or ``None`` for irregular grids.
   * - ``geography.distinct_longitudes``
     - 1-D array of unique longitude values for regular grids, or ``None`` for irregular grids.
   * - ``geography.x``
     - Array of x-coordinates in the native CRS. ``dtype`` argument supported.
   * - ``geography.y``
     - Array of y-coordinates in the native CRS. ``dtype`` argument supported.
   * - ``geography.shape``
     - Grid shape as a tuple of integers (e.g. ``(latitude_size, longitude_size)``).
   * - ``geography.projection``
     - :py:class:`~earthkit.data.utils.projections.Projection` object describing the CRS, or ``None``.
   * - ``geography.bounding_box``
     - :py:class:`~earthkit.data.utils.bbox.BoundingBox` for the grid extent.
   * - ``geography.area``
     - Bounding box as a ``(north, west, south, east)`` tuple of floats.
   * - ``geography.grid_type``
     - String identifying the grid type (e.g. ``"regular_ll"``, ``"reduced_gg"``).
   * - ``geography.grid_spec``
     - Grid specification. Can be used to construct a new geography of the same type.
   * - ``geography.grid``
     - Grid definition understood by eckit-geo (when grid support is available).
   * - ``geography.unique_grid_id``
     - A hashable identifier that is the same for two fields sharing an identical grid.


How-tos
-------

- :ref:`/how-tos/field/field_overview.ipynb`
- :ref:`/how-tos/grib/grib_overview.ipynb`
- :ref:`/how-tos/grib/grib_lat_lon_value_ll.ipynb`
- :ref:`/how-tos/grib/grib_lat_lon_value_rgg.ipynb`
- :ref:`/how-tos/grib/grib_nearest_gridpoint.ipynb`
- :ref:`/how-tos/misc/projection.ipynb`
