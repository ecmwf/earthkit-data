.. _field_concept:

Field
=====

A :py:class:`~earthkit.data.core.field.Field` represents a single horizontal slice of a
geophysical quantity at a particular time and vertical level. It is the fundamental data
structure in EarthKit Data and bundles together:

- the **data values** — a 2-D (or 1-D unstructured) array of floating-point numbers;
- a set of **metadata components** that fully describe the field (see below).

Fields are created automatically when reading data through
:py:func:`~earthkit.data.from_source` and are normally accessed as members of a
:py:class:`~earthkit.data.core.fieldlist.FieldList`. See :doc:`fieldlist` for how to work
with collections of fields.


Component-based metadata
------------------------

The Field class is not polymorphic. Instead it is composed of a set of replaceable,
polymorphic *components*, each responsible for a distinct aspect of the metadata:

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Attribute
     - Component class
     - What it describes
   * - ``field.parameter``
     - :py:class:`~earthkit.data.field.component.parameter.ParameterBase`
     - Physical quantity: variable name, units, CF names, chemical or optical properties.
   * - ``field.time``
     - :py:class:`~earthkit.data.field.component.time.TimeBase`
     - Temporal coordinate: base datetime, forecast step, valid datetime.
   * - ``field.vertical``
     - :py:class:`~earthkit.data.field.component.vertical.VerticalBase`
     - Vertical coordinate: level value, level type, layer bounds.
   * - ``field.geography``
     - :py:class:`~earthkit.data.field.component.geography.GeographyBase`
     - Horizontal grid: lat/lon arrays, bounding box, projection, grid type.
   * - ``field.ensemble``
     - :py:class:`~earthkit.data.field.component.ensemble.EnsembleBase`
     - Ensemble member identifier.
   * - ``field.proc``
     - :py:class:`~earthkit.data.field.component.proc.ProcBase`
     - Post-processing operations applied to produce the field (e.g. accumulation).

Each component exposes its metadata through named methods (e.g.
``field.vertical.level()``) and through the generic
:meth:`~earthkit.data.core.field.Field.get` method using a ``"component.key"`` prefix:

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> field = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
    >>> field.parameter.variable()
    '2t'
    >>> field.get("parameter.variable")
    '2t'
    >>> field.vertical.level()
    0
    >>> field.get("time.base_datetime")
    datetime.datetime(2020, 1, 1, 0, 0)

For a full description of each component's available keys see the dedicated pages:
:doc:`parameter`, :doc:`time`, :doc:`vertical`, :doc:`geography`, :doc:`ensemble`,
and :doc:`proc`.


Immutability of field values
-----------------------------

Field values are immutable: :meth:`~earthkit.data.core.field.Field.values` always returns
a **copy** of the underlying array. Modifications to that copy do not affect the stored
data. This guarantees that the original data remains consistent no matter how many
downstream operations consume it.


Modifying a field
-----------------

Because both values and metadata are immutable, changes are expressed by creating a
new field via :meth:`~earthkit.data.core.field.Field.set`. The method accepts a dictionary
of ``"component.key": value`` pairs (and/or a ``"values"`` entry) and returns a new field
with the requested changes applied while leaving all other attributes unchanged:

.. code-block:: python

    >>> new_field = field.set({"vertical.level": 500, "time.step": 6})
    >>> new_field.vertical.level()
    500
    >>> new_field.time.step()
    datetime.timedelta(seconds=21600)


Arithmetic operations
----------------------

Fields support element-wise arithmetic directly (``+``, ``-``, ``*``, ``/``). Each
operation returns a new field whose data is the result of the operation. The metadata
(parameter, time, vertical, geography, ensemble, proc) of the **left-hand operand** is
retained in the result without modification:

.. code-block:: python

    >>> fl = ekd.from_source("sample", "tuv_pl.grib").to_fieldlist()
    >>> result = fl[0] + fl[1]
    >>> result.parameter.variable() == fl[0].parameter.variable()
    True


How-tos
-------

- :ref:`/how-tos/field/field_overview.ipynb`
- :ref:`/how-tos/grib/grib_overview.ipynb`
- :ref:`/how-tos/grib/grib_modify_values.ipynb`
- :ref:`/how-tos/grib/grib_modify_metadata.ipynb`
