.. _data-access:

Data access
=================

.. _data_values:

Accessing data with ``.to_numpy()`` and ``.values``
-----------------------------------------------------

We can extract the values from data objects as an ndarray using the ``.to_numpy()`` method or the ``.values`` property.

When an earthkit-data :ref:`sources <data-sources>` provides a list of fields, these methods can be called both on the whole object and on the individual fields, too. While ``.to_numpy()``, by default, preserves the shape of the fields,  ``.values`` always returns a flat array per field. By using ``flatten=True``, we can force ``.to_numpy()`` to return a flat ndarray per field.

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

Accessing metadata with ``.metadata()``
-----------------------------------------------------
