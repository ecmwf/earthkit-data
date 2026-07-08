.. _field_concept:

Field
=====

A :py:class:`~earthkit.data.core.field.Field` represents a single horizontal slice of a
geophysical quantity at a particular time and vertical level. It is the fundamental data
structure in earthkit-data and bundles together:

- the **data values** — a 2-D (or 1-D unstructured) array of floating-point numbers;
- a set of format independent **metadata components** that fully describe the field (see :ref:`below <field_concept_component-metadata>`). This metadata is often referred to as the "high-level" metadata in the earthkit documentation.
- raw metadata (e.g. ecCodes GRIB keys) from the original data source, when available.

Fields are created automatically when reading data through
:py:func:`~earthkit.data.from_source` and are normally accessed as members of a
:py:class:`~earthkit.data.core.fieldlist.FieldList`. Refer to the
:ref:`FieldList concept page <fieldlist_concept>` for a full description of how to
select, iterate over, and manipulate collections of fields.

.. _field_concept_component-metadata:

High-level metadata
---------------------------------------

The Field class is not polymorphic. Instead it is composed of a set of replaceable,
polymorphic *components*, each responsible for a distinct aspect of the metadata.

.. admonition:: List of high-level metadata keys
   :class: note

   See the list of all available component metadata keys in :ref:`field_keys`.


The following table lists the components that make up a field and the corresponding
classes that implement them. Use the ``Reference`` column to jump to the component's dedicated page for a full description of its keys.

.. list-table::
   :header-rows: 1
   :widths: 20 40 15 25

   * - Attribute
     - What it describes
     - Reference
     - Component class
   * - ``field.parameter``
     - Physical quantity: variable name, units, CF names, chemical or optical properties.
     - :doc:`parameter`
     - :py:class:`~earthkit.data.field.component.parameter.ParameterBase`
   * - ``field.time``
     - Temporal coordinate: base datetime, forecast step, valid datetime.
     - :doc:`time`
     - :py:class:`~earthkit.data.field.component.time.TimeBase`
   * - ``field.vertical``
     - Vertical coordinate: level value, level type, layer bounds.
     - :doc:`vertical`
     - :py:class:`~earthkit.data.field.component.vertical.VerticalBase`
   * - ``field.geography``
     - Horizontal grid: lat/lon arrays, bounding box, projection, grid type.
     - :doc:`geography`
     - :py:class:`~earthkit.data.field.component.geography.GeographyBase`
   * - ``field.ensemble``
     - Ensemble member identifier.
     - :doc:`ensemble`
     - :py:class:`~earthkit.data.field.component.ensemble.EnsembleBase`
   * - ``field.proc``
     - Post-processing operations applied to produce the field (e.g. accumulation).
     - :doc:`proc`
     - :py:class:`~earthkit.data.field.component.proc.ProcBase`
   * - ``field.labels``
     - User-defined key-value pairs; keys are arbitrary strings chosen by the caller.
     - :doc:`labels`
     - :py:class:`~earthkit.data.field.handler.labels.SimpleLabels`

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

The metadata keys can be used in :meth:`~earthkit.data.core.fieldlist.FieldList.sel` and :meth:`~earthkit.data.core.fieldlist.FieldList.order_by` to select and sort fields.


Raw metadata
------------

The term "raw metadata" refers to the metadata available in the data object the field was created from. Currently, it is only available when the field is created from a GRIB message. The raw metadata can be accessed through the :meth:`~earthkit.data.core.field.Field.get` method using the ``"metadata.<key>"`` prefix. For example, we can access the ecCodes GRIB ``"shortName"`` key using:

.. code-block:: python

    >>> field.get("metadata.shortName")
    '2t'

Alternatively, the :meth:`~earthkit.data.core.field.Field.metadata` method can also be used to access the raw metadata with or without a prefix. Actually, this method can only be used to access raw metadata. For example, we can access the ecCodes GRIB ``"shortName"`` key using:

.. code-block:: python

    >>> field.metadata("shortName")
    '2t'
    >>> field.metadata("metadata.shortName")
    '2t'

There is a major difference between the two methods: the :meth:`~earthkit.data.core.field.Field.metadata` method will raise a :py:class:`KeyError` if the key is not found, while the :meth:`~earthkit.data.core.field.Field.get` method allows to specify a default value to return if the key is not found. For example, if the field does not have raw (GRIB) metadata:

.. code-block:: python

    >>> field.get("metadata.shortName")
    None

    >>> field.get("metadata.shortName", default="N/A")
    'N/A'

    >>> field.metadata("shortName")
    Traceback (most recent call last):
        ...
    KeyError: 'shortName'


The raw metadata, when available, can also be used in methods such as  :meth:`~earthkit.data.core.fieldlist.FieldList.sel` and  :meth:`~earthkit.data.core.fieldlist.FieldList.order_by` by using the ``"metadata.<key>"`` prefix. For example, to select all fields with an ecCodes GRIB short name of ``"2t"``:

.. code-block:: python

    >>> fl = ekd.from_source("sample", "test.grib").to_fieldlist()
    >>> fl_sel = fl.sel({"metadata.shortName": "2t"})
    >>> len(fl_sel)
    1
    >>> fl_sel[0].get("metadata.shortName")
    '2t'


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

- :ref:`/tutorials/field/field_overview.ipynb`
- :ref:`/tutorials/grib/grib_overview.ipynb`
- :ref:`/tutorials/grib/grib_modify_values.ipynb`
- :ref:`/tutorials/grib/grib_modify_metadata.ipynb`
