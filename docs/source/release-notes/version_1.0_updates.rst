.. _release-notes-1.0:

Version 1.0 Updates
///////////////////////

.. note::

    This release contains breaking changes. Please refer to the
    :ref:`migration guide <migration_1.0.0>` for a full description of what has changed
    and how to update your code.


Version 1.0.0
==============

New features
++++++++++++

Data object returned by ``from_source``
----------------------------------------

:py:func:`~earthkit.data.from_source` now returns a lightweight *data object* instead of
a format-specific fieldlist. The data object defers actual loading until it is converted
to a concrete representation via one of the ``to_*`` methods (e.g.
:meth:`~earthkit.data.Data.to_fieldlist`, :meth:`~earthkit.data.Data.to_xarray`,
:meth:`~earthkit.data.Data.to_numpy`). The available conversions for a given source can be
inspected via :py:attr:`~earthkit.data.Data.available_types`.

See :ref:`migration_1.0.0` for migration details.

Notebook examples:

- :ref:`/tutorials/source/data.ipynb`


Component-based Field metadata
-------------------------------

:py:class:`~earthkit.data.core.field.Field` has been redesigned around a set of
format-independent, polymorphic *components*, each responsible for a distinct aspect of
the field's metadata:

- :ref:`parameter_component`     — physical quantity, units, CF names; extended with chemical, optical, and wave-spectra sub-types.
- :ref:`time_component`     — base datetime, forecast step, valid datetime.
- :ref:`vertical_component` — level value, level type, layer bounds, parametric (hybrid) level coefficients.
- :ref:`geography_component` — lat/lon arrays, bounding box, projection, grid type.
- :ref:`ensemble_component` — ensemble member identifier.
- :ref:`proc_component` — post-processing operations (e.g. accumulation type and time span).

Components are accessed via field attributes (e.g. ``field.time``) or through the generic
:meth:`~earthkit.data.core.field.Field.get` method using ``"component.key"`` strings. Raw
source-native keys (e.g. GRIB ``shortName``) remain accessible via
:meth:`~earthkit.data.core.field.Field.metadata` or with the ``"metadata."`` prefix in
:meth:`~earthkit.data.core.field.Field.get`.

See the :ref:`field_concept` page for full details.

Notebook examples:

- :ref:`/tutorials/field/field_overview.ipynb`
- :ref:`/tutorials/grib/grib_overview.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_chem.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_wave_spectra.ipynb`


Field modification via ``set()``
---------------------------------

Fields can now be modified in a non-destructive way using
:py:meth:`~earthkit.data.core.field.Field.set`. The method accepts a dictionary of
``"component.key": value`` pairs (and/or a ``"values"`` entry) and returns a **new** field
with the requested changes applied, leaving the original unchanged.

See the how-to notebooks:

- :ref:`/tutorials/grib/grib_modify_metadata.ipynb`
- :ref:`/tutorials/grib/grib_modify_values.ipynb`


Field and FieldList arithmetic
--------------------------------

Element-wise arithmetic operators (``+``, ``-``, ``*``, ``/``) are now supported directly
on both :py:class:`~earthkit.data.core.field.Field` and
:py:class:`~earthkit.data.core.fieldlist.FieldList` objects. Each operation returns a new
object with the computed values; the metadata of the left-hand operand is preserved in the
result.

.. note::

    The ``+`` operator no longer concatenates fieldlists. Use
    :py:func:`~earthkit.data.concat` for concatenation instead.

Notebook examples:

- :ref:`/tutorials/field/field_overview.ipynb`
- :ref:`/tutorials/field/field_arithmetic.ipynb`
- :ref:`/tutorials/field/field_assign_constant_value.ipynb`
- :ref:`/tutorials/grib/grib_overview.ipynb`


Xarray engine
-----------------------------------------

The Xarray engine has been refactored and a new default profile ``earthkit`` has been
added. This profile uses the format-independent component metadata keys to build dataset
dimensions and coordinates, making it consistent across GRIB, NetCDF, and other sources.
The legacy ``mars`` and ``grib`` profiles are retained.

Other notable Xarray engine changes:

- Four new built-in dimensions were added to support the extended parameter component
  metadata (:pr:`1008`):

  - ``chem_variable`` — chemical constituent or aerosol type
  - ``wavelength`` — central wavelength for optical parameters
  - ``wave_direction`` — wave propagation direction for 2-D wave spectra
  - ``wave_frequency`` — wave frequency for 2-D wave spectra

  CF-compliant attributes are set on the corresponding coordinate variables automatically.

- The ``"number"`` dimension role has been renamed to ``"member"``.
- The ``time_dim_mode`` kwarg has been replaced by ``time_dims``.
- The ``_earthkit`` dataset attribute is now serialised as a JSON string, enabling
  round-trip NetCDF serialisation without removing it  (:pr:`1021`).
- Added the ``aux_coords`` keyword argument to specify 1- or multi-dimensional auxiliary coordinate variables whose values are derived from any metadata key (:pr:`969`).
- Added the ``reference_field`` property to the Xarray ``earthkit`` accessor to allow getting
  the reference field of the dataarray. Also added the ``set`` method to allow setting the
  reference field of the dataarray using a Field or any args/kwargs accepted by :func:`~earthkit.data.core.field.Field.set` (:pr:`990`).
- Allowed using null values in datetime related objects (:pr:`999`).

See :ref:`xr_engine` for full documentation.

Notebook examples:

- :ref:`/tutorials/xr_engine/xarray_engine_overview.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_temporal.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_ensemble.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_chem.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_wave_spectra.ipynb`


Dependencies
+++++++++++++++

Geography support for GRIB data — including access to latitudes, longitudes, grid
specification, and other grid properties via the
:py:class:`~earthkit.data.field.component.geography.GeographyBase` component — requires
the `eccodes <https://github.com/ecmwf/eccodes>`_ binaries built with
`eckit <https://github.com/ecmwf/eckit>`_ geo support. Without it, geography keys will
return ``None`` or raise an error.
