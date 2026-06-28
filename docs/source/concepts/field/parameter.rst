.. _parameter_component:

Parameter component
===================

Every :py:class:`~earthkit.data.core.field.Field` carries a *parameter component* that describes
the physical quantity the field represents. The parameter component is accessible via the
:attr:`parameter` attribute of a field and is represented by a subclass of
:py:class:`~earthkit.data.field.component.parameter.ParameterBase`.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> field = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
    >>> field.parameter.variable()
    '2t'
    >>> field.parameter.units()
    K
    >>> field.parameter.standard_name()
    '2_metre_temperature'

The same information is available through the generic :meth:`~earthkit.data.core.field.Field.get`
interface using the ``"parameter."`` prefix:

.. code-block:: python

    >>> field.get("parameter.variable")
    '2t'
    >>> field.get("parameter.units")
    K

The parameter component is **immutable**. Use the
:meth:`~earthkit.data.field.component.parameter.ParameterBase.set` method (or
:meth:`~earthkit.data.core.field.Field.set` on the field) to derive a modified copy:

.. code-block:: python

    >>> new_field = field.set({"parameter.variable": "msl", "parameter.units": "Pa"})
    >>> new_field.parameter.variable()
    'msl'


Parameter types
---------------

The appropriate parameter subclass is determined automatically from the data:

- :py:class:`~earthkit.data.field.component.parameter.Parameter` — standard meteorological
  parameter with a variable name and units.
- :py:class:`~earthkit.data.field.component.parameter.ChemicalParameter` — parameter that
  also carries a chemical constituent or aerosol type (``chem`` / ``chem_long_name`` keys).
- :py:class:`~earthkit.data.field.component.parameter.OpticalParameter` — parameter defined
  at a specific wavelength (``wavelength``, ``wavelength_bounds``, ``wavelength_units`` keys).
- :py:class:`~earthkit.data.field.component.parameter.ChemicalOpticalParameter` — combines
  both chemical and optical information.
- :py:class:`~earthkit.data.field.component.parameter.WaveSpectraParameter` — 2-D wave spectra
  parameter carrying direction and frequency bins (``wave_direction*`` and
  ``wave_frequency*`` keys).


Accessing parameter information
--------------------------------

All parameter keys are accessible through :meth:`~earthkit.data.core.field.Field.get` with the
``"parameter."`` prefix, and can therefore be used in
:meth:`~earthkit.data.core.fieldlist.FieldList.sel`,
:meth:`~earthkit.data.core.fieldlist.FieldList.order_by`, and
:meth:`~earthkit.data.core.fieldlist.FieldList.metadata`.

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Key
     - Description
   * - ``parameter.variable``
     - Parameter variable name as a string (e.g. ``"2t"``). Not normalised; taken directly from the source data. For example, for GRIB data, it will be the value of the "shortName" key in the GRIB message.
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


How-tos
-------

- :ref:`/how-tos/field/field_overview.ipynb`
- :ref:`/how-tos/grib/grib_overview.ipynb`
- :ref:`/how-tos/xr_engine/xarray_engine_chem.ipynb`
- :ref:`/how-tos/xr_engine/xarray_engine_wave_spectra.ipynb`
