.. _field_keys:

Metadata key reference
====================================================

This page lists all **high-level** (format independent) metadata keys that can be accessed via
:meth:`~earthkit.data.core.field.Field.get` and used in
:meth:`~earthkit.data.core.fieldlist.FieldList.sel` and
:meth:`~earthkit.data.core.fieldlist.FieldList.order_by`.

Keys follow the ``"<component>.<name>"`` naming convention.  Each section
below corresponds to one component; click the component heading to go to its
dedicated page.


.. _field_keys_parameter:

:doc:`Parameter <parameter>`
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Key
     - Description
   * - ``parameter.variable``
     - Parameter variable name as a string (e.g. ``"2t"``). Not normalised; taken directly from the source data.
   * - ``parameter.param``
     - Alias of ``parameter.variable``.
   * - ``parameter.standard_name``
     - CF standard name of the parameter variable.
   * - ``parameter.long_name``
     - CF long name of the parameter variable.
   * - ``parameter.units``
     - Units of the parameter as a :py:class:`~earthkit.utils.units.Units` object.
   * - ``parameter.chem``
     - Chemical constituent or aerosol type, or ``None`` for non-chemical parameters.
   * - ``parameter.chem_long_name``
     - Long name of the chemical constituent or aerosol type, or ``None``.
   * - ``parameter.wavelength``
     - Central wavelength for optical parameters, or ``None``. Accepts an optional ``units`` argument for conversion.
   * - ``parameter.wavelength_bounds``
     - Wavelength bounds as a 2-tuple for optical parameters, or ``None``.
   * - ``parameter.wavelength_units``
     - Units of the wavelength (e.g. nanometres), or ``None``.
   * - ``parameter.wave_direction``
     - Wave propagation direction for 2-D wave spectra parameters, or ``None``.
   * - ``parameter.wave_direction_index``
     - 0-based index of the wave direction bin, or ``None``.
   * - ``parameter.wave_direction_bounds``
     - Direction bounds as a 2-tuple, or ``None``.
   * - ``parameter.wave_direction_units``
     - Units of the wave direction (e.g. degrees), or ``None``.
   * - ``parameter.wave_frequency``
     - Wave frequency for 2-D wave spectra parameters, or ``None``.
   * - ``parameter.wave_frequency_index``
     - 0-based index of the wave frequency bin, or ``None``.
   * - ``parameter.wave_frequency_bounds``
     - Frequency bounds as a 2-tuple, or ``None``.
   * - ``parameter.wave_frequency_units``
     - Units of the wave frequency (e.g. 1/s), or ``None``.


.. _field_keys_time:

:doc:`Time <time>`
-------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Key
     - Description
   * - ``time.base_datetime``
     - The base (reference) datetime of the forecast as a :py:class:`datetime.datetime`.
   * - ``time.forecast_reference_time``
     - Alias of ``time.base_datetime``.
   * - ``time.base_date``
     - The date part of the base datetime as a :py:class:`datetime.date`.
   * - ``time.base_time``
     - The time-of-day part of the base datetime as a :py:class:`datetime.time`.
   * - ``time.valid_datetime``
     - The valid datetime (``base_datetime + step``) as a :py:class:`datetime.datetime`.
   * - ``time.step``
     - The forecast step as a :py:class:`datetime.timedelta`. Integer values are interpreted as hours.
   * - ``time.forecast_period``
     - Alias of ``time.step``.
   * - ``time.forecast_month``
     - The forecast month as an integer. Only available for monthly forecast time; returns ``None`` otherwise.
   * - ``time.indexing_datetime``
     - The indexing datetime used for ordering within a dataset. Returns ``None`` for types that do not define it.


.. _field_keys_vertical:

:doc:`Vertical <vertical>`
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Key
     - Description
   * - ``vertical.level``
     - Scalar level value in the native units of the level type.
   * - ``vertical.level_type``
     - Level type name as a string (e.g. ``"pressure"``).
   * - ``vertical.layer``
     - Layer bounds as a ``(bottom, top)`` tuple, or ``None`` for non-layer types.
   * - ``vertical.abbreviation``
     - Abbreviation of the level type (e.g. ``"pl"``).
   * - ``vertical.units``
     - Units of the level value.
   * - ``vertical.positive``
     - Positive direction of the coordinate (``"up"``, ``"down"``, or ``None``).
   * - ``vertical.cf``
     - Dictionary of CF metadata (``standard_name``, ``long_name``, ``units``, ``positive``).
   * - ``vertical.parametric``
     - ``True`` if the level type is parametric (e.g. hybrid levels).
   * - ``vertical.coefficients``
     - Coefficient arrays for parametric level types, ``None`` otherwise.
   * - ``vertical.coefficient_names``
     - Names of the coefficients for parametric level types, ``None`` otherwise.
   * - ``vertical.number_of_levels``
     - Number of model levels for parametric level types, ``None`` otherwise.


.. _field_keys_geography:

:doc:`Geography <geography>`
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

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
     - Grid shape as a tuple of integers (e.g. ``(latitude_size, longitude_size)`` for a 2-D lat/lon grid).
   * - ``geography.projection``
     - :py:class:`~earthkit.data.utils.projections.Projection` object describing the CRS, or ``None``.
   * - ``geography.bounding_box``
     - :py:class:`~earthkit.data.utils.bbox.BoundingBox` for the grid extent.
   * - ``geography.area``
     - Bounding box as a ``(north, west, south, east)`` tuple of floats.
   * - ``geography.grid_type``
     - String identifying the grid type (e.g. ``"regular_ll"``, ``"reduced_gg"``).
   * - ``geography.grid_spec``
     - Grid specification. Can be used to construct a new geography of the same type. Experimental; may not be available for all geography types.
   * - ``geography.grid``
     - ``eckit.geo.Grid`` object. Experimental; may not be available for all geography types.
   * - ``geography.unique_grid_id``
     - A hashable identifier that is the same for two fields sharing an identical grid.


.. _field_keys_ensemble:

:doc:`Ensemble <ensemble>`
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Key
     - Description
   * - ``ensemble.member``
     - Ensemble member identifier as a string, or ``None`` for deterministic data.
   * - ``ensemble.realization``
     - Alias of ``ensemble.member``.
   * - ``ensemble.realisation``
     - Alias of ``ensemble.member``.


.. _field_keys_proc:

:doc:`Processing (proc) <proc>`
--------------------------------

.. warning::

  This component is experimental and may be changed in future versions of earthkit-data.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Key
     - Description
   * - ``proc.time``
     - The first :py:class:`~earthkit.data.field.component.proc.TimeProcItem` in the processing
       list, or ``None`` if no time processing is present.
   * - ``proc.time_value``
     - The time-span value from the first time processing item as a :py:class:`datetime.timedelta`,
       or ``None``.
   * - ``proc.time_method``
     - The processing method from the first time processing item as a
       :py:class:`~earthkit.data.field.component.time_span.TimeMethod`, or ``None``.


.. _field_keys_labels:

:doc:`Labels <labels>`
-----------------------

Labels use ``"labels.<user_key>"`` where *user_key* is any string chosen by the
caller.  There are no predefined keys; every key-value pair is user-supplied.

.. code-block:: python

    >>> field.get("labels.my_key")
    >>> field.set({"labels.my_key": "value"})

See :doc:`labels` for the full API and usage examples.
