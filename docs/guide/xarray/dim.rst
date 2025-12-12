.. _xr_dim:

Dimensions
==================

One of the most important aspect of the :ref:`xr_engine` is how it generates dimensions in the Xarray dataset with :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray`.

.. _xr_dim_roles:
.. _xr_predefined_dims:


Predefined dimensions and dimension roles
-------------------------------------------

By default, the following predefined dimensions are generated, in the following order:

- ensemble forecast member dimension
- temporal dimensions (controlled by ``time_dim_mode``)
- vertical dimensions (controlled by ``level_dim_mode``)

The predefined dimensions are based on the ``dim_roles``, which is a mapping between the "roles" and the metadata keys.
The possible roles are as follows:

.. list-table:: Default dimension roles
   :header-rows: 1

   * - Dimension role
     - Description
     - Key (profile: :ref:`mars <xr_profile_mars>`)
     - Key (profile: :ref:`grib <xr_profile_grib>`)
   * - "number"
     - metadata key interpreted as ensemble forecast members
     - "number"
     - "number"
   * - "date"
     - metadata key interpreted as date part of the "forecast_reference_time"
     - "date"
     - "date"
   * - "time"
     - metadata key interpreted as time part of the "forecast_reference_time"
     - "time"
     - "time"
   * - "step"
     - metadata key interpreted as forecast step
     - "step_timedelta"
     - "step_timedelta"
   * - "forecast_reference_time"
     - if not specified or None or empty the forecast reference time is built using the "date" and "time" roles
     - None
     - None
   * - "valid_time"
     - if not specified or None or empty the valid time is built using the "validityDate" and "validityTime" metadata keys
     - None
     - None
   * - "level"
     - metadata key interpreted as level
     - "levelist"
     - "level"
   * - "level_type"
     - metadata key interpreted as level type
     - "levtype"
     - "typeOfLevel"

By default, the dimension names are the same as the role names. To use the associated metadata keys instead use the ``dim_name_from_role_name=False`` option.

.. note::

    For GRIB data, "step_timedelta" is a generated metadata key (by earthkit-data), which is the representation of the value of the "endStep" key as a `datetime.timedelta`.


Dimension modes
----------------------

The ensemble forecast member dimension is a single dimension named "number" by default, unless ``dim_roles`` defines it differently and ``dim_name_from_role_name=False``.

The case of temporal and vertical dimensions is more involved. Both type of dimensions can be generated in multiple ways, and can be represented
by multiple individual dimensions in an Xarray dataset.
The ``time_dim_mode`` and ``level_dim_mode`` options control what temporal and vertical dimensions are generated in the Xarray dataset,
while ``dim_roles`` (together with ``dim_name_from_role_name``) control their names and the way their coordinates are formed.


.. list-table:: Temporal dimensions modes
   :header-rows: 1

   * - ``time_dim_mode``
     - Dimensions
   * - "forecast" (default)
     - "forecast_reference_time", "step"
   * - "valid_time"
     - "valid_time"
   * - "raw"
     - "date", "time", "step"


See the following examples:
- :ref:`/examples/xarray_engine_temporal.ipynb`
- :ref:`/examples/xarray_engine_seasonal.ipynb`


.. list-table:: Vertical dimensions modes
   :header-rows: 1

   * - ``level_dim_mode``
     - Dimensions
     - Remarks
   * - "level" (default)
     - "level", "level_type"
     - The "level_type"`dimension usually has size 1, so it is removed (squeezed) by default.
   * - "level_per_type"
     - "<level_per_type>"
     - This is a template dimension which in the Xarray dataset is materialised under the name being the value
       of the metadata key referred by ``dim_roles["level_type"]`` (e.g. "surface", "meanSea", "isobaricInhPa", "hybrid", etc.).
       The coordinates are formed from the metadata key referred by ``dim_roles["level"]``
   * - "level_and_type"
     - "level_and_type"
     - The coordinates are formed by concatenating the values of the metadata keys ``dim_roles["level"]``
       and ``dim_roles["level_type"]`` (e.g. "850isobaricInhPa", "137hybrid", "0surface")


See the following example:
- :ref:`/examples/xarray_engine_level.ipynb`


Squeezing/ensuring dimensions
----------------------------------

By default, the dimensions are squeezed. This means that if a dimension has only one value, it is removed from the dataset.
This can be controlled with the ``squeeze`` option.
Alternatively, the ``ensure_dims`` option can be used to ensure that certain dimensions are always present in the dataset,
even if they have only one value. This is useful when you want to keep the dimensions for consistency or for further processing.

See the following notebook for examples of how this works:

- :ref:`/examples/xarray_engine_squeeze.ipynb`


Turning a size-1 dimension to an attribute
---------------------------------------------

Alternatively to squeezing, a size-1 dimension can be also converted into a variable attribute using the ``dims_as_attrs`` option.
This can be useful when for example dealing with single-level variables defined on different levels (e.g. ``"heightAboveGround": 2``, ``"meanSea": 0``, etc.).
Similarly to ``squeeze=True``, it allows to avoid a problem of incompatible coordinates of a size-1 dimension,

to preserve the information on coordinates and at the same time avoid a problem of incompatibility of coordinates
across variables which would otherwise prevent from creating an Xarray Dataset.

Note that it is possible to combine this option with ``ensure_dims`` to have a size-1 dimension *preserved* and
*converted* into a variable attribute.

See the following notebook for details:

- :ref:`/examples/xarray_engine_dims_as_attrs.ipynb`


Extra dimensions
----------------------

The ``extra_dims`` option allows to add extra dimensions to the Xarray dataset on top of the predefined ones.



Remapping keys and template dimensions
----------------------------------------

TODO: Explain that remapping keys and the template dimension "<level_per_type>" can be used in ``ensure_dims``, ``dims_as_attrs`` and ``extra_dims``
(and maybe ``drop_dims``; but, does it make sense?)



Fixed dimensions
---------------------

TODO: Check how it works and its interplay with ``extra_dims``, ``squeeze``, ``ensure_dims``, ``dims_as_attrs``, ``drop_dims``, ``rename_dims``.


Renaming dimensions
------------------------

Here explain how ``rename_dims`` works. In particular discuss the case when ``level_dim_mode="level_per_type"`` and we want to rename, say, "surface" dimension.


Dropping dimensions
------------------------

Can one use the template dimension "<level_per_type>"? Or, say, "surface"?
