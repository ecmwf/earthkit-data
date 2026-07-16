.. _vertical_component:

Vertical component and metadata keys
===========================================

Every :py:class:`~earthkit.data.core.field.Field` carries a *vertical component* that describes
where in the atmosphere, ocean, or land the field is defined. The vertical component is accessible
via the :attr:`vertical` attribute of a field and is represented by a
:py:class:`~earthkit.data.field.component.vertical.Vertical` object (or its parametric subclass
for hybrid levels).

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> field = ekd.from_source("sample", "tuv_pl.grib").to_fieldlist()[0]
    >>> field.vertical.level()
    1000
    >>> field.vertical.level_type()
    'pressure'
    >>> field.vertical.units()
    hPa
    >>> field.vertical.positive()
    'down'

The same information is available through the generic :meth:`~earthkit.data.core.field.Field.get`
interface using the ``"vertical."`` prefix:

.. code-block:: python

    >>> field.get("vertical.level")
    1000
    >>> field.get("vertical.level_type")
    'pressure'

The vertical component is **immutable**. Use the :meth:`~earthkit.data.field.component.vertical.Vertical.set`
method (or :meth:`~earthkit.data.core.field.Field.set` on the field) to derive a modified copy:

.. code-block:: python

    >>> new_field = field.set({"vertical.level": 500})
    >>> new_field.vertical.level()
    500


Level types
-----------

The *level type* classifies the nature of the vertical coordinate. It is represented by a
:py:class:`~earthkit.data.field.component.level_type.LevelType` object, which carries the
following metadata:

- **name** – canonical identifier used throughout earthkit-data (e.g. ``"pressure"``)
- **abbreviation** – short label (e.g. ``"pl"``)
- **standard_name** – CF standard name (e.g. ``"air_pressure"``)
- **long_name** – human-readable description
- **units** – native units of the level value
- **layer** – ``True`` only when both the bottom and top bounding surfaces are defined, i.e. the level type describes a proper layer between two bounds; ``False`` when only one or neither bounding surface is specified (see for example ``"low_cloud_layer"`` vs ``"medium_cloud_layer"``)
- **level** – indicates which bound is the *representative* level: ``"top"``, ``"bottom"``, or ``None``  when undefined
- **positive** – vertical direction in which values increase: ``"up"``, ``"down"``, or ``None`` when undefined

When earthkit-data encounters a level type that is not in the predefined list below, it is
automatically registered at runtime so that arbitrary model-specific level types are handled
transparently.


Predefined level types
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 22 16 14 14 8 6 8 12

   * - Name
     - CF standard name
     - Long name
     - Abbreviation
     - Units
     - Layer
     - Level
     - Positive
   * - ``abstract_single_level``
     -
     - abstract single level
     - ``abstractSingleLevel``
     -
     - No
     -
     -
   * - ``cloud_base``
     -
     - cloud base
     - ``cloudBase``
     -
     - No
     -
     -
   * - ``depth_below_land_layer``
     - depth
     - soil depth
     - ``d_bll_layer``
     - m
     - Yes
     - top
     - down
   * - ``depth_below_land_level``
     - depth
     - soil depth
     - ``d_bll``
     - m
     - No
     -
     - down
   * - ``depth_below_sea_layer``
     - depth
     - depth
     - ``d_bsl_layer``
     - m
     - Yes
     - bottom
     - down
   * - ``entire_atmosphere``
     -
     - entire atmosphere
     - ``entire_atmosphere``
     -
     - No
     -
     -
   * - ``entire_lake``
     -
     - entire lake
     - ``entireLake``
     -
     - No
     -
     -
   * - ``entire_melt_pond``
     -
     - entire melt pond
     - ``entireMeltPond``
     -
     - No
     -
     -
   * - ``general``
     -
     - general
     - ``gen``
     - 1
     - No
     -
     - down
   * - ``height_above_ground_level``
     - height
     - height above the surface
     - ``h_agl``
     - m
     - No
     -
     - up
   * - ``height_above_mean_sea_level``
     - height_above_mean_sea_level
     - height above mean sea level
     - ``h_asl``
     - m
     - No
     -
     - up
   * - ``high_cloud_layer``
     -
     - high cloud layer
     - ``highCloudLayer``
     - hPa
     - No
     -
     - down
   * - ``hybrid``
     - atmosphere_hybrid_sigma_pressure_coordinate
     - hybrid level
     - ``ml``
     - 1
     - No
     -
     - down
   * - ``ice_layer_on_water``
     -
     - ice layer on water
     - ``iceLayerOnWater``
     -
     - No
     -
     -
   * - ``ice_top_on_water``
     -
     - ice top on water
     - ``iceTopOnWater``
     -
     - No
     -
     -
   * - ``lake_bottom``
     -
     - lake bottom
     - ``lakeBottom``
     -
     - No
     -
     -
   * - ``low_cloud_layer``
     -
     - low cloud layer
     - ``lowCloudLayer``
     - hPa
     - No
     - bottom
     - down
   * - ``mean_sea``
     -
     - mean sea level
     - ``mean_sea``
     -
     - No
     -
     -
   * - ``medium_cloud_layer``
     -
     - medium cloud layer
     - ``mediumCloudLayer``
     - hPa
     - Yes
     - bottom
     - down
   * - ``mixed_layer_depth_by_density``
     -
     - mixed layer depth by density
     - ``mixedLayerDepthByDensity``
     - kg m-3
     - No
     -
     - down
   * - ``mixed_layer_parcel``
     -
     - mixed layer parcel
     - ``mixedLayerParcel``
     - Pa
     - No
     -
     - down
   * - ``mixing_layer``
     - mixing_layer
     - mixing layer
     - ``mixingLayer``
     -
     - No
     -
     -
   * - ``most_unstable_parcel``
     -
     - most unstable parcel
     - ``mostUnstableParcel``
     -
     - No
     -
     -
   * - ``nominal_top_of_atmosphere``
     -
     - nominal top of atmosphere
     - ``nominalTopOfAtmosphere``
     -
     - No
     -
     -
   * - ``ocean_model``
     -
     - ocean model
     - ``oceanModel``
     - 1
     - No
     -
     - down
   * - ``ocean_model_layer``
     -
     - ocean model layer
     - ``oceanModelLayer``
     - 1
     - Yes
     - bottom
     - down
   * - ``ocean_surface``
     -
     - ocean surface
     - ``ocean_surface``
     -
     - No
     -
     -
   * - ``ocean_surface_to_bottom``
     -
     - ocean surface to bottom
     - ``oceanSurfaceToBottom``
     -
     - No
     -
     -
   * - ``potential_temperature``
     - air_potential_temperature
     - air_potential temperature
     - ``pt``
     - K
     - No
     -
     -
   * - ``potential_vorticity``
     - ertel_potential_vorticity
     - potential vorticity
     - ``pv``
     - nK m2 kg-1 s-1
     - No
     -
     -
   * - ``pressure``
     - air_pressure
     - pressure
     - ``pl``
     - hPa
     - No
     -
     - down
   * - ``pressure_layer``
     - air_pressure
     - pressure
     - ``p_layer``
     - hPa
     - Yes
     - top
     - down
   * - ``sea_ice_layer``
     -
     - sea ice layer
     - ``seaIceLayer``
     - 1
     - Yes
     - bottom
     - down
   * - ``snow``
     -
     - snow layer
     - ``snow``
     - 1
     - Yes
     - bottom
     - down
   * - ``snow_layer_over_ice_on_water``
     -
     - snow layer over ice on water
     - ``snowLayerOverIceOnWater``
     -
     - No
     -
     -
   * - ``soil_layer``
     -
     - soil layer
     - ``soilLayer``
     - 1
     - Yes
     - bottom
     - down
   * - ``stratosphere``
     -
     - stratosphere
     - ``stratosphere``
     -
     - No
     -
     -
   * - ``surface``
     - surface
     - surface
     - ``sfc``
     -
     - No
     -
     -
   * - ``temperature``
     - air_temperature
     - temperature
     - ``isothermal``
     - K
     - No
     -
     -
   * - ``tropopause``
     -
     - tropopause
     - ``tropopause``
     -
     - No
     -
     -
   * - ``troposphere``
     -
     - troposphere
     - ``troposphere``
     -
     - No
     -
     -
   * - ``unknown``
     -
     - unknown
     - ``unknown``
     -
     - No
     -
     -
   * - ``water_surface_to_isothermal_ocean_layer``
     -
     - water surface to isothermal ocean layer
     - ``waterSurfaceToIsothermalOceanLayer``
     -
     - No
     -
     -


Layers
------

When ``layer`` is ``True``, the vertical component stores two bounding level values rather than a
single value. The ``level`` attribute (and the ``"vertical.level"`` key) returns the *representative*
scalar level, derived from either the top or the bottom bound depending on the *Level* column in the
table above. The full pair of bounds is available via
:meth:`~earthkit.data.field.component.vertical.Vertical.layer`.


Parametric levels
-----------------

The ``hybrid`` level type is *parametric*: the actual pressure at any grid point must be computed
from a set of coefficients (``A`` and ``B``) together with the surface pressure field. For hybrid
levels the vertical component exposes the following additional methods:

- :meth:`~earthkit.data.field.component.vertical.VerticalBase.coefficients` – the ``A`` and ``B``
  coefficient arrays
- :meth:`~earthkit.data.field.component.vertical.VerticalBase.coefficient_names` – the names of
  the coefficients (``("A", "B")``)
- :meth:`~earthkit.data.field.component.vertical.VerticalBase.number_of_levels` – total number of
  model levels

List of vertical metadata keys
--------------------------------

Supported keys:

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Key
     - Description
   * - ``vertical.level``
     - Scalar level value in the native units of the level type
   * - ``vertical.level_type``
     - Level type name as a string (e.g. ``"pressure"``)
   * - ``vertical.layer``
     - Layer bounds as a ``(bottom, top)`` tuple, or ``None`` for non-layer types
   * - ``vertical.abbreviation``
     - Abbreviation of the level type (e.g. ``"pl"``)
   * - ``vertical.units``
     - Units of the level value
   * - ``vertical.positive``
     - Positive direction of the coordinate (``"up"``, ``"down"``, or ``None``)
   * - ``vertical.cf``
     - Dictionary of CF metadata (``standard_name``, ``long_name``, ``units``, ``positive``)
   * - ``vertical.parametric``
     - ``True`` if the level type is parametric (e.g. hybrid levels)
   * - ``vertical.coefficients``
     - Coefficient arrays for parametric level types, ``None`` otherwise
   * - ``vertical.coefficient_names``
     - Names of the coefficients for parametric level types, ``None`` otherwise
   * - ``vertical.number_of_levels``
     - Number of model levels for parametric level types, ``None`` otherwise


Tutorials / How-tos
-------

- :ref:`/tutorials/field/field_overview.ipynb`
- :ref:`/tutorials/grib/grib_overview.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_level.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_field_dims.ipynb`
