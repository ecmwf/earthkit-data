.. _xr_dim:

Dimensions
==================

One of the most important aspect of the :ref:`xr_engine` is how it generates dimensions in the Xarray dataset with :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray`.

.. _xr_dim_roles:
.. _xr_predefined_dims:


Predefined dimensions and dimension roles
-------------------------------------------

By default, a list of predefined dimensions are generated. Their order is fixed:

- ensemble forecast member dimension
- temporal dimensions (controlled by ``time_dim_mode``)
- vertical dimensions (controlled by ``level_dim_mode``)

The predefined dimensions are based on the ``dim_roles``, which is a mapping between the "roles" and the metadata keys associated with the roles.
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

the metadata keys. However, this can be controlled with the ``dim_name_from_role_name`` option. If set to ``False``, the dimension names will be the same as the dimension roles. This is useful when you want to use the dimension roles in your code, as they are more descriptive than the metadata keys.

.. note::

    For GRIB data, "step_timedelta" is a generated metadata key (by earthkit-data), which is the representation of the value of the "endStep" key as a `datetime.timedelta`.


Dimension modes
----------------------

The ``time_dim_mode`` and ``level_dim_mode`` options control how the temporal and vertical dimensions are generated in the Xarray dataset using ``dim_roles``. See the following notebooks for examples of how these modes work:

``time_dim_mode``:

- :ref:`/examples/xr_engine_temporal.ipynb`
- :ref:`/examples/xr_engine_seasonal.ipynb`


``level_dim_mode``:
- :ref:`/examples/xr_engine_level.ipynb`


Squeezing/ensuring dimensions
----------------------------------

By default, the dimensions are squeezed. This means that if a dimension has only one value, it is removed from the dataset. This can be controlled with the ``squeeze`` option. Alternatively, the ``ensure_dims`` option can be used to ensure that certain dimensions are always present in the dataset, even if they have only one value. This is useful when you want to keep the dimensions for consistency or for further processing.

See the following notebooks for examples of how this works:

- :ref:`/examples/xr_engine_squeeze.ipynb`


Extra dimensions
----------------------

The ``extra_dims`` option allows to add extra dimensions to the Xarray dataset on top of the predefined ones.
