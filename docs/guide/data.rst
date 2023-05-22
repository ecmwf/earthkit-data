.. _data-object:

Data objects
=================

.. _base-class-methods:

Base class methods
~~~~~~~~~~~~~~~~~~~~

When we call :func:`from_source <data-sources>` it will return a **data object**. The actual object type depends on the source parameters and the data we read but all of t
them will be derived from the :obj:`Base <data.core.Base>`, which defines an :obj:`common set of methods <data.core.Base>`. As a minimum, data objects try to implement these methods, but some will only be available for certain data types. Some objects offer an extra set of methods on top of the common methods.

Method overview
~~~~~~~~~~~~~~~~~~

The data types can be grouped into two main categories offering a different set of methods:

:ref:`Field data <field-data>` has a rich API including:

  - :ref:`conversion to scientific Python objects <transform>` e.g to xarray or pandas
  - :ref:`iteration <iter>`
  - :ref:`slicing <slice>`
  - :ref:`filtering <sel>`
  - :ref:`ordering <order_by>`
  - :ref:`data value access <data_values>`
  - :ref:`metadata access <metadata>`
  - :ref:`inspection <inspection>`

:ref:`Non-field data <non-field-data>` (e.g. observation/points) offers a :ref:`conversion <transform>` to a pandas DataFrame via the ``.to_pandas()`` method.

.. _transform:

Conversion to scientific Python objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can **convert** data objects into familiar scientific Python objects (including numpy arrays, pandas dataframes, xarray datasets):

.. code-block:: python

    ds.to_xarray()  # for field data
    ds.to_pandas()  # for non-field data
    ds.to_numpy()  # when the data is a n-dimensional array.


.. _iter:

Iterating
~~~~~~~~~

When an earthkit-data data `source` or dataset provides a list of fields, it can be iterated over to access each field (in a given order see :ref:`below <order_by>`).

In the the following example we read a GRIB file from disk. In the iteration each element is a field (representing a GRIB message):

.. code-block:: python

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")

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

.. _slice:

Selection with ``[...]``
~~~~~~~~~~~~~~~~~~~~~~~~

When an earthkit-data data `source` or dataset provides a list of fields, a subset of the list can be created using the standard python list interface relying on brackets and slices. A subsetting also works by providing a list or ndarray of indices.

.. code-block:: python

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")

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

When an earthkit-data data `source` or dataset provides a list of fields, the method ``.sel()`` allows filtering this list and we can **select a subset** of the list of fields. ``.sel()`` returns a "view" so no new data is generated on disk or in memory. The selection offers the same functionality as the original data object, so methods like ``.to_numpy()``, ``.to_xarray()``, etc. are all available.

``.sel()`` conditions are specified by a set of **metadata** keys. Both single or multiple keys are allowed to use and each can specify the following type of filter values:

 - single value
 - list of values
 - slice of values (defines a **closed interval**, so treated as inclusive of both the start and stop values, unlike normal Python indexing)

The following example demonstrates the usage of ``.sel()``. The input data contains temperature and wind fields on various pressure levels.

.. code-block:: python

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")

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

.. .. _isel:

.. Selection with ``.isel()``
.. ~~~~~~~~~~~~~~~~~~~~~~~~~~

.. When an earthkit-data data `source` or dataset provides a list of fields, the method ``.isel()`` allows filtering this list and we can **select a subset** of the list of fields. ``.isel()`` returns a "view" so no new data is generated on disk or in memory. The selection offers the same functionality as the original data object, so methods like ``.to_numpy()``, ``.to_xarray()`` , etc. are all available.

.. ``.isel()`` works similarly to :ref:`sel <sel>` but conditions are specified by indices of metadata keys. A metadata index stores the unique, **sorted** values of the corresponding metadata key in the input data. To list the indices that have more than one values use the ``.indices`` property, or to find out the values of a specific index use ``.index()``.

.. Both single or multiple metadata keys are allowed to use in ``.isel()`` and each can specify the following type of index values:

..  - single index
..  - list of indices
..  - slice of indices (behaves like normal Python indexing, stop value not included)

.. The following example demonstrates the usage of ``.isel()``. The input data contains temperature and wind fields on various pressure levels.

.. .. code:: python

..     >>> import earthkit.data
..     >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")

..     >>> len(ds)
..     18
..     >>> ds.indices
..     {'levelist': (1000, 850, 700, 500, 400, 300), 'param': ('t', 'u', 'v')}

..     >>> subset = ds.isel(param=0)
..     >>> len(ds)
..     6

..     >>> for f in subset:
..     ...     print(f)
..     ...
..     GribField(t,1000,20180801,1200,0,0)
..     GribField(t,850,20180801,1200,0,0)
..     GribField(t,700,20180801,1200,0,0)
..     GribField(t,500,20180801,1200,0,0)
..     GribField(t,400,20180801,1200,0,0)
..     GribField(t,300,20180801,1200,0,0)

..     >>> subset = ds.isel(param=[1, 2], level=slice(2, 4))
..     >>> len(subset)
..     4

..     >>> for f in subset:
..     ...     print(f)
..     ...
..     GribField(u,700,20180801,1200,0,0)
..     GribField(v,700,20180801,1200,0,0)
..     GribField(u,500,20180801,1200,0,0)
..     GribField(v,500,20180801,1200,0,0)


.. _order_by:

Ordering with ``.order_by()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an earthkit-data data `source` or dataset provides a list of fields, the method ``.order_by()`` allows sorting this list.

``.order_by()`` returns a "view" so no new data is generated on disk or in memory. The resulting object offers the same functionality as the original data object, so methods like ``.to_numpy()``, ``.to_xarray()``, etc. are all available.

.. code-block:: python

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")

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

Accessing data with ``.to_numpy()`` and ``.values``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can extract the values from data objects as an ndarray using the ``.to_numpy()`` method or the ``.values`` property.

When an earthkit-data :ref:`source <data-sources>` provides a list of fields, these methods can be called both on the whole object and on the individual fields, too.

While ``.to_numpy()``, by default, preserves the shape of the fields,  ``.values`` always returns a flat array per field. By using ``flatten=True``, we can force ``.to_numpy()`` to return a flat ndarray per field.

In the following example the input GRIB data contains 6 fields each defined on a latitude-longitude grid with a shape of (7, 12).

.. code-block:: python

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")

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

Accessing metadata ``.metadata()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can extract metadata from data objects using the ``.metadata()`` method.

When an earthkit-data :ref:`source <data-sources>` provides a list of fields, this method can be called both on the whole object and on the individual fields, too.

.. _inspection:

Inspection
~~~~~~~~~~~~~

On certain data objects (currently only :ref:`grib` and :ref:`bufr`) we can call ``.ls()``, ``.head()`` or ``.tail()``.
