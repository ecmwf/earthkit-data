.. _fieldlist_concept:

FieldList
=========

A :py:class:`~earthkit.data.core.fieldlist.FieldList` is an ordered, indexable collection of
:py:class:`~earthkit.data.core.field.Field` objects. It is the primary interface returned by
:py:func:`~earthkit.data.from_source` and acts as the main entry point for working with
multi-field datasets in EarthKit Data.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("sample", "tuv_pl.grib").to_fieldlist()
    >>> len(ds)
    18
    >>> ds[0]
    GribField(u, 1000, 2020-01-01 00:00, 0, None, None)


Indexing and slicing
--------------------

FieldLists support integer indexing and Python slice notation. Slicing returns a new
FieldList containing the selected fields:

.. code-block:: python

    >>> ds[0]           # single field
    >>> ds[0:3]         # slice — returns a FieldList
    >>> ds[-1]          # last field


Iteration
---------

Iterating over a FieldList yields individual
:py:class:`~earthkit.data.core.field.Field` objects one at a time:

.. code-block:: python

    >>> for field in ds:
    ...     print(field.parameter.variable(), field.vertical.level())


Selection
---------

:meth:`~earthkit.data.core.fieldlist.FieldList.sel` filters a FieldList by metadata values and
returns a new FieldList containing only the matching fields. Keys follow the
``"component.key"`` convention used throughout EarthKit Data:

.. code-block:: python

    >>> pl500 = ds.sel({"vertical.level": 500})
    >>> wind = ds.sel({"parameter.variable": ["u", "v"]})

Source-native keys (e.g. GRIB ``shortName``, ``level``) can also be used by prefixing them
with ``"metadata."``:

.. code-block:: python

    >>> plt500 = ds.sel({"metadata.shortName": "t", "metadata.level": 500})


Ordering
--------

:meth:`~earthkit.data.core.fieldlist.FieldList.order_by` returns a new FieldList sorted by
one or more metadata keys. Multiple keys can be passed as a list and are applied in order:

.. code-block:: python

    >>> ds_sorted = ds.order_by(["parameter.variable", "vertical.level"])


Metadata access
---------------

:meth:`~earthkit.data.core.fieldlist.FieldList.get` returns a list of metadata values,
one per field, using the ``"component.key"`` keys described in the component pages:

.. code-block:: python

    >>> ds.get("parameter.variable")
    ['u', 'v', 't', ...]
    >>> ds.get(["parameter.variable", "vertical.level"])
    [('u', 1000), ('v', 1000), ('t', 1000), ...]

For source-native keys (e.g. GRIB ``shortName``, ``level``),
:meth:`~earthkit.data.core.fieldlist.FieldList.metadata` can be used directly without any
prefix:

.. code-block:: python

    >>> ds.metadata("shortName")
    ['u', 'v', 't', ...]

The :meth:`~earthkit.data.core.fieldlist.FieldList.ls` method provides a quick tabular
summary of the most commonly used metadata keys, In Jupyter notebooks, the output is rendered as a table; in other environments e.g. terminal, it has to be printed with ``print()`` to see the table:


.. code-block:: python

    >>> ds.ls() # in Jupyter notebook, this is rendered as a table

.. code-block:: python

    >>> print(ds.ls()) # in terminal, an extra print() is needed to render the table

Extracting data
---------------

:meth:`~earthkit.data.core.fieldlist.FieldList.to_numpy` returns the field values stacked
into a NumPy array and accepts ``dtype``, ``copy``, and other arguments. The shape of the
result depends on the shape of the individual fields:

- for fields with a 1-D grid (e.g. unstructured grids), the result has shape
  ``(number_of_fields, number_of_grid_points)``;
- for fields with a 2-D grid (e.g. regular lat/lon grids), the result has shape
  ``(number_of_fields, Ny, Nx)``.

By default a **copy** of the data is returned. Pass ``copy=False`` to avoid the copy when
the data layout allows it; note that a copy may still be made if the underlying source
cannot provide a zero-copy view:

.. code-block:: python

    >>> ds.to_numpy(dtype="float32").shape
    (18, 19, 36)
    >>> ds.to_numpy(copy=False).shape
    (18, 19, 36)

:attr:`~earthkit.data.core.fieldlist.FieldList.values` is a convenience property that
always returns a 2-D array of shape ``(number_of_fields, number_of_grid_points)``,
where each row is the flat 1-D array of values for one field. The array type matches the
native array format of the underlying data (e.g. NumPy for GRIB and NetCDF fields, or a
GPU array for array-backed FieldLists). Each access returns a **copy**:

.. code-block:: python

    >>> ds.values.shape
    (18, 684)


Converting to Xarray
--------------------

:meth:`~earthkit.data.core.fieldlist.FieldList.to_xarray` converts the FieldList to an
:py:class:`xarray.Dataset`. EarthKit Data uses a dedicated Xarray engine that maps
field metadata to dataset dimensions and coordinates:

.. code-block:: python

    >>> xr_ds = ds.to_xarray()
    >>> xr_ds
    <xarray.Dataset>
    Dimensions:  ...


Concatenation
-------------

Two FieldLists can be concatenated with the ``+`` operator, producing a new FieldList that
contains all fields from both operands in order:

.. code-block:: python

    >>> combined = ds1 + ds2
    >>> len(combined) == len(ds1) + len(ds2)
    True


FieldList types
---------------

There are several concrete FieldList implementations, each suited to a different access
pattern:

- **SimpleFieldList** — in-memory list, produced by most operations such as
  :meth:`sel`, :meth:`order_by`, and ``+``.
- **StreamFieldList** — backed by a streaming source (e.g. FDB or URL stream). Supports
  forward iteration only; use :meth:`to_fieldlist` with ``read_all=True`` to materialise
  into memory.
- **ArrayFieldList** — backed by NumPy arrays, used when constructing fields
  programmatically.
- **FileFieldList** — backed by an on-disk file (e.g. a cached GRIB file).


How-tos
-------

- :ref:`/how-tos/field/field_overview.ipynb`
- :ref:`/how-tos/grib/grib_overview.ipynb`
- :ref:`/how-tos/grib/grib_selection.ipynb`
- :ref:`/how-tos/grib/grib_order_by.ipynb`
- :ref:`/how-tos/xr_engine/xarray_engine_overview.ipynb`
