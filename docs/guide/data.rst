.. _data-object:

Data objects
=================

When we call :func:`from_source` it will return a **data object**. The actual object type depends on the source parameters and the :ref:`data format <data-format>`, but is supposed to implement a **common** set of methods/operators, some of which will only be available for certain :ref:`data types <data-format>`.

The list of common methods/operators:

  - :ref:`conversion`
  - :ref:`concat`
  - :ref:`iter`
  - :ref:`batched`
  - :ref:`group_by`
  - :ref:`slice`
  - :ref:`sel`
  - :ref:`order_by`
  - :ref:`data_values`
  - :ref:`metadata`
  - :ref:`inspection`

.. _conversion:

Conversion to scientific Python objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can **convert** data objects into familiar scientific Python objects (including numpy arrays, pandas dataframes, xarray datasets):

.. code-block:: python

    ds.to_xarray()  # for field data
    ds.to_pandas()  # for non-field data
    ds.to_numpy()  # when the data is a n-dimensional array.

.. _concat:

Concatenation
~~~~~~~~~~~~~~~~~~

Data objects can be concatenated with the "+" operator:

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds1 = ekd.from_source("file", "docs/examples/test.grib")
    >>> len(ds1)
    2
    >>> ds2 = ekd.from_source("file", "docs/examples/test6.grib")
    >>> len(ds2)
    6
    >>> ds = ds1 + ds2
    >>> len(ds)
    8

.. _iter:

Iteration
~~~~~~~~~

When an earthkit-data data `source` or dataset provides a :class:`~data.core.fieldlist.FieldList` or message list, we can iterate through it to access each element (in a given order see :ref:`below <order_by>`).

In the the following example we read a GRIB file from disk. In the iteration each element is a field (representing a GRIB message):

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("file", "docs/examples/test6.grib")

    >>> len(ds)
    6

    >>> for f in ds:
    ...     print(f)
    ...
    GribField(t,1000,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)
    GribField(u,850,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)

.. _batched:

Iteration with ``.batched()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an earthkit-data data `source` or dataset provides a :class:`~data.core.fieldlist.FieldList` or message list, we can iterate through it in batches of fixed size using :meth:`~data.core.fieldlist.FieldList.batched`. This method also works for :ref:`streams <streams>`.

In the the following example we read a GRIB file from disk and iterate through it in batches of 2. Each iteration step yields a :class:`~data.core.fieldlist.FieldList` of 2 fields.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("file", "docs/examples/test6.grib")

    >>> for f in ds.batched(2):
    ...     print(f"len={len(f)} {f.metadata(('param', 'level'))}")
    ...
    len=2 [('t', 1000), ('u', 1000)]
    len=2 [('v', 1000), ('t', 850)]
    len=2 [('u', 850), ('v', 850)]


.. _group_by:

Iteration with ``.group_by()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an earthkit-data data `source` or dataset provides a :class:`~data.core.fieldlist.FieldList` or message list, we can iterate through it in groups defined by metadata keys using :meth:`~data.core.fieldlist.FieldList.group_by`. This method also works for :ref:`streams <streams>`.

In the the following example we read a GRIB file from disk and iterate through it in groups defined by the "level" metadata key. Each iteration step yields a :class:`~data.core.fieldlist.FieldList` containing fields with the same "level" value.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("file", "docs/examples/test6.grib")

    >>> for f in ds.group_by("level"):
    ...     print(f"len={len(f)} {f.metadata(('param', 'level'))}")
    ...
    len=3 [('t', 1000), ('u', 1000), ('v', 1000)]
    len=3 [('t', 850), ('u', 850), ('v', 850)]


.. _slice:

Selection with ``[...]``
~~~~~~~~~~~~~~~~~~~~~~~~

When an earthkit-data data `source` or dataset provides a :class:`~data.core.fieldlist.FieldList` or message list, a subset of it can be created using the standard python list interface relying on brackets and slices. Slicing also works by providing a list or ndarray of indices.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("file", "docs/examples/test6.grib")

    >>> len(ds)
    6

    >>> ds[0]
    GribField(t,1000,20180801,1200,0,0)

    >>> for f in ds[0:3]:
    ...     print(f)
    GribField(t,1000,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)

    >>> for f in ds[0:4:2]:
    ...     print(f)
    GribField(t,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)

    >>> ds[-1]
    GribField(v,850,20180801,1200,0,0)

    >>> for f in ds[-2:]:
    ...     print(f)
    GribField(u,850,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)

    >>> for f in ds[[1, 3]]:
    ...     print(f)
    ...
    GribField(u,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)

    >>> for f in ds[np.array([1, 3])]:
    ...     print(f)
    ...
    GribField(u,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)


.. _sel:

Selection with ``.sel()``
~~~~~~~~~~~~~~~~~~~~~~~~~

When an earthkit-data data `source` or dataset provides a :class:`~data.core.fieldlist.FieldList` or message list, the method ``.sel()`` allows filtering this list and we can **select a subset** of the list. ``.sel()`` returns a view to original data, so no data is copied. The selection offers the same functionality as the original data object, so methods like ``.to_numpy()``, ``.to_xarray()``, etc. are all available.

For more details see: :meth:`~data.core.fieldlist.FieldList.sel`.

The following example demonstrates the usage of ``.sel()``. The input data contains temperature and wind fields on various pressure levels.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("file", "docs/examples/tuv_pl.grib")

    >>> len(ds)
    18

    >>> subset = ds.sel(param="t")
    >>> len(subset)
    6

    >>> for f in subset:
    ...     print(f)
    ...
    GribField(t,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)
    GribField(t,700,20180801,1200,0,0)
    GribField(t,500,20180801,1200,0,0)
    GribField(t,400,20180801,1200,0,0)
    GribField(t,300,20180801,1200,0,0)

    >>> subset = ds.sel(param=["u", "v"], level=slice(400, 700))
    >>> len(subset)
    6

    >>> for f in subset:
    ...     print(f)
    ...
    GribField(u,700,20180801,1200,0,0)
    GribField(v,700,20180801,1200,0,0)
    GribField(u,500,20180801,1200,0,0)
    GribField(v,500,20180801,1200,0,0)
    GribField(u,400,20180801,1200,0,0)
    GribField(v,400,20180801,1200,0,0)

.. _isel:

Selection with ``.isel()``
~~~~~~~~~~~~~~~~~~~~~~~~~~

When an earthkit-data data `source` or dataset provides a :class:`~data.core.fieldlist.FieldList`, the method ``.isel()`` allows filtering this list and we can **select a subset** of the list. ``.isel()`` returns a view to the original data, so no data is copied. The selection offers the same functionality as the original data object, so methods like ``.to_numpy()``, ``.to_xarray()`` , etc. are all available.

``.isel()`` works similarly to :ref:`sel <sel>` but conditions are specified by indices of metadata keys. A metadata index stores the unique, **sorted** values of the corresponding metadata key from all the fields in the input data.

For more details see: :meth:`~data.core.fieldlist.FieldList.isel`

The following example demonstrates the usage of ``.isel()``. The input data contains temperature and wind fields on various pressure levels.

.. code:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("file", "docs/examples/tuv_pl.grib")

    >>> len(ds)
    18
    >>> ds.indices
    {'levelist': (1000, 850, 700, 500, 400, 300), 'param': ('t', 'u', 'v')}

    >>> subset = ds.isel(param=0)
    >>> len(ds)
    6

    >>> for f in subset:
    ...     print(f)
    ...
    GribField(t,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)
    GribField(t,700,20180801,1200,0,0)
    GribField(t,500,20180801,1200,0,0)
    GribField(t,400,20180801,1200,0,0)
    GribField(t,300,20180801,1200,0,0)

    >>> subset = ds.isel(param=[1, 2], level=slice(2, 4))
    >>> len(subset)
    4

    >>> for f in subset:
    ...     print(f)
    ...
    GribField(u,700,20180801,1200,0,0)
    GribField(v,700,20180801,1200,0,0)
    GribField(u,500,20180801,1200,0,0)
    GribField(v,500,20180801,1200,0,0)


.. _order_by:

Ordering with ``.order_by()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an earthkit-data data `source` or dataset provides a :class:`~data.core.fieldlist.FieldList` or message list, the method ``.order_by()`` allows sorting this list.

``.order_by()`` returns a "view" so no new data is generated on disk or in memory. The resulting object offers the same functionality as the original data object, so methods like ``.to_numpy()``, ``.to_xarray()``, etc. are all available.

For more details see: :meth:`~data.core.fieldlist.FieldList.order_by`

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("file", "docs/examples/test6.grib")

    >>> len(ds)
    6

    >>> for f in ds.order_by("param"):
    ...     print(f)
    ...
    GribField(t,850,20180801,1200,0,0)
    GribField(t,1000,20180801,1200,0,0)
    GribField(u,850,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)

    >>> for f in ds.order_by(["level", "param"]):
    ...     print(f)
    ...
    GribField(t,850,20180801,1200,0,0)
    GribField(u,850,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)
    GribField(t,1000,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)

    >>> for f in ds.order_by(param=["u", "t", "v"]):
    ...     print(f)
    ...
    GribField(u,850,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)
    GribField(t,1000,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)


.. _data_values:

Accessing data values
~~~~~~~~~~~~~~~~~~~~~~~~

We can extract the values from data objects as an ndarray using the ``.to_numpy()`` method or the ``.values`` property.

When an earthkit-data :ref:`source <data-sources>` provides a :class:`~data.core.fieldlist.FieldList`, these methods can be called both on the whole object and on the individual fields, too.

While ``.to_numpy()``, by default, preserves the shape of the fields,  ``.values`` always returns a flat array per field. By using ``flatten=True``, we can force ``.to_numpy()`` to return a flat ndarray per field.

For more details see: :meth:`~data.core.fieldlist.FieldList.to_numpy`.

In the following example the input GRIB data contains 6 fields each defined on a latitude-longitude grid with a shape of (7, 12).

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("file", "docs/examples/test6.grib")

    >>> ds.to_numpy().shape
    (6, 7, 12)
    >>> ds.to_numpy(flatten=True).shape
    (6, 84)
    >>> ds.values.shape
    (6, 84)

    >>> for f in ds:
    ...     f.values.shape
    ...
    (84,)
    (84,)
    (84,)
    (84,)
    (84,)
    (84,)

    >>> for f in ds:
    ...     f.to_numpy().shape
    ...
    (7, 12)
    (7, 12)
    (7, 12)
    (7, 12)
    (7, 12)
    (7, 12)

.. _metadata:

Accessing metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~

We can extract metadata from data objects using the ``.metadata()`` method.

When an earthkit-data :ref:`source <data-sources>` provides a :class:`~data.core.fieldlist.FieldList` or message list, this method can be called both on the whole object and on the individual fields, too.

For more details see: :meth:`FieldList.metadata() <data.core.fieldlist.FieldList.metadata>` and
:meth:`Field.metadata() <data.core.fieldlist.Field.metadata>`

.. _inspection:

Inspecting contents
~~~~~~~~~~~~~~~~~~~~~~~~

On certain data objects (currently only :ref:`grib` and :ref:`bufr`) we can call ``.ls()``, ``.head()`` or ``.tail()``.

For more details see: :meth:`~data.core.fieldlist.FieldList.ls`.
