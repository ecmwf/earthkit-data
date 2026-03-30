.. _xr_dim:

Dimensions
==================

One of the most important aspect of the :ref:`Xarray engine <xr_engine>` is how it generates dimensions in the Xarray dataset with :py:meth:`~earthkit.data.indexing.xarray.XarrayMixIn.to_xarray`.

.. _xr_dim_roles:
.. _xr_predefined_dims:


Predefined dimensions and dimension roles
-------------------------------------------

By default, the following predefined dimensions are generated, in the following order:

- ensemble forecast member dimension
- temporal dimensions, controlled by ``time_dim_mode``  (see details :ref:`here <xr_time_dim_modes>`)
- vertical dimensions, controlled by ``level_dim_mode`` (see details :ref:`here <xr_level_dim_modes>`)

The predefined dimensions are based on the ``dim_roles``, which is a mapping between the "roles" and the metadata keys. This mapping is defined for each :ref:`profile <xr_profile>` and can be customised by the user. The possible roles are as follows:

.. list-table:: Default dimension roles
   :header-rows: 1

   * - Dimension role
     - Description
     - Metadata key (in default profile: :ref:`earthkit <xr_profile_earthkit>`)
   * - "member"
     - Ensemble forecast member
     - "ensemble.member"
   * - "date"
     - Date part of the ``"forecast_reference_time"``. This dimension is used when ``time_dim_mode="raw"``. When None, it is generated from the date part of ``forecast_reference_time``.
     - None
   * - "time"
     - Time part of the ``"forecast_reference_time"``. This dimension is used when ``time_dim_mode="raw"``. When None, it is generated from the time part of ``forecast_reference_time``.
     - None
   * - "step"
     - Forecast step
     - "time.step"
   * - "forecast_reference_time"
     -  Forecast reference time (base datetime). Can be a single  metadata key, or a list/tuple of two metadata keys representing the "date" and "time" parts of the forecast reference time. Alternatively, it can be a dict with "date" and "time" keys specifying the corresponding metadata keys. Used when ``time_dim_mode="forecast"``.
     - "time.forecast_reference_time"
   * - "valid_time"
     - Valid datetime. Used when ``time_dim_mode="valid_time"`` or ``add_valid_time_coord=True``.
     - "time.valid_datetime"
   * - "level"
     - Level
     - "vertical.level"
   * - "level_type"
     - Level type
     - "vertical.level_type"

By default, the dimension names are the same as the role names. To use the associated metadata keys instead use the ``dim_name_from_role_name=False`` option.

.. .. note::

..     For GRIB data, ``"step_timedelta"`` is a generated metadata key (by earthkit-data), which is the representation of the value of the ``"endStep"`` key as a ``datetime.timedelta``.


.. _xr_ensemble_member_dim:

Ensemble member dimension
----------------------------

The ensemble member dimension is a single dimension named ``"member"`` by default, unless ``dim_roles`` defines it differently or ``dim_name_from_role_name=False``.

.. _xr_time_dim_modes:

Temporal dimension modes
--------------------------------------

The temporal dimensions can be generated in multiple ways, and can be represented by multiple individual dimensions in an Xarray dataset.
The ``time_dim_mode`` option controls what temporal dimensions are generated in the Xarray dataset,
while ``dim_roles`` (together with ``dim_name_from_role_name``) controls their names and the way their coordinates are formed.


.. list-table:: Temporal dimensions modes
   :header-rows: 1

   * - ``time_dim_mode``
     - Dimensions generated
   * - "forecast" (default)
     - "forecast_reference_time", "step"
   * - "valid_time"
     - "valid_time"
   * - "raw"
     - "date", "time", "step"


The following examples demonstrate the temporal dimensions modes:

- :ref:`/how-tos/xr_engine/xarray_engine_temporal.ipynb`
- :ref:`/how-tos/xr_engine/xarray_engine_seasonal.ipynb`


.. _xr_level_dim_modes:

Vertical dimension modes
--------------------------------------

The vertical dimensions can be generated in multiple ways, and can be represented by multiple individual dimensions in an Xarray dataset.
The ``level_dim_mode`` option controls what vertical dimensions are generated in the Xarray dataset,
while ``dim_roles`` (together with ``dim_name_from_role_name``) controls their names and the way their coordinates are formed.


.. list-table:: Vertical dimensions modes
   :header-rows: 1

   * - ``level_dim_mode``
     - Dimensions generated
     - Remarks
   * - "level" (default)
     - "level", "level_type"
     - The "level_type" dimension usually has size 1, so it is squeezed by default.
   * - "level_per_type"
     - "<level_per_type>"
     - Uses a template dimension that is materialised in the Xarray dataset
       under the name given by the value of the metadata key referenced by
       "dim_roles["level_type"]" (for example "surface",
       "mean_sea", "pressure", "hybrid").
   * - "level_and_type"
     - "level_and_type"
     - Creates a single dimension whose coordinates are formed by
       concatenating the values of the metadata keys
       "dim_roles["level"]" and "dim_roles["level_type"]"
       (for example "850pressure", "137hybrid",
       "0surface").


The following example demonstrates the vertical dimensions modes:

- :ref:`/how-tos/xr_engine/xarray_engine_level.ipynb`


.. _xr_squeeze_and_ensure_dims:


Squeezing/ensuring dimensions
----------------------------------

By default, the dimensions are squeezed. This means that if a dimension has only one value, it is removed from the dataset.
This can be controlled with the ``squeeze`` option. Alternatively, the ``ensure_dims`` option can be used to ensure that certain dimensions are always present in the dataset, even if they have only one value. This is useful when you want to keep the dimensions for consistency or for further processing.

See the following notebook for examples of how this works:

- :ref:`/how-tos/xr_engine/xarray_engine_squeeze.ipynb`


.. _xr_dims_as_attrs:


Size-1 dimensions as variable attributes
---------------------------------------------

As an alternative to squeezing, a size-1 dimension can be converted into
a variable attribute using the ``dims_as_attrs`` option. This is
particularly useful when working with single-level variables defined on
different vertical levels (for example,
``"mean_sea": 0``).

Like ``squeeze=True``, this approach avoids issues caused by incompatible
coordinates on size-1 dimensions. In addition, it preserves the
associated coordinate information by storing it as a variable
attribute.

The ``dims_as_attrs`` option can also be combined with ``ensure_dims``,
allowing a size-1 dimension to be both preserved as a dimension and
exposed as a variable attribute.

For a detailed discussion and examples, see the following notebook:

- :ref:`/how-tos/xr_engine/xarray_engine_dims_as_attrs.ipynb`


Extra dimensions
----------------------

The ``extra_dims`` option allows additional dimensions to be introduced
into the resulting Xarray dataset, beyond :ref:`the predefined dimensions <xr_predefined_dims>`.

Each entry in ``extra_dims`` refers to a metadata key whose values are
used as the coordinates of a newly created dimension.

Extra dimensions are handled in the same way as predefined dimensions: if an extra dimension has size 1, it can be
:ref:`squeezed or ensured <xr_squeeze_and_ensure_dims>`, or :ref:`converted into a variable attribute <xr_dims_as_attrs>`.

For a detailed discussion and examples, see the following notebook:

- :ref:`/how-tos/xr_engine/xarray_engine_extra_dims.ipynb`


Remapping
-------------

The ``remapping`` option allows virtual metadata keys to be defined by combining existing metadata keys.
These virtual keys can then be used in the same way as native metadata keys throughout the Xarray engine configuration.

In particular, a virtual metadata key can be used:

- as a dimension, by including it in ``extra_dims`` or ``ensure_dims``; once defined as a dimension,
  it can also be referenced in ``dims_as_attrs`` like any other dimension;

- as a custom variable name, by specifying it in the ``variable_key`` option.

For a detailed discussion and examples, see the following notebook:

- :ref:`/how-tos/xr_engine/xarray_engine_remapping.ipynb`
