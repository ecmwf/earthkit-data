.. _concat:

Concatenating data objects
============================

:func:`~earthkit.data.utils.concat.concat` takes two or more objects and combines them into a single
one. It is the recommended way to combine already-loaded data objects.

Here ``ds1`` and ``ds2`` are :py:class:`Data <earthkit.data.data.Data>` objects (each a ``GribData``,
since they are single-file, single-format sources), and the result ``ds`` is again a ``Data`` object:

.. code-block:: python

    import earthkit.data as ekd

    ds1 = ekd.from_source("file", "a.grib")  # Data object (GribData)
    ds2 = ekd.from_source("file", "b.grib")  # Data object (GribData)

    ds = ekd.concat(ds1, ds2)  # Data object (GribData)

More than two objects can be combined in a single call:

.. code-block:: python

    ds3 = ekd.from_source("file", "c.grib")  # Data object (GribData)
    ds = ekd.concat(ds1, ds2, ds3)  # Data object (GribData)

``concat`` also works directly on :class:`~earthkit.data.core.fieldlist.FieldList` objects, in which case
the result is a ``FieldList`` too:

.. code-block:: python

    fl1 = ds1.to_fieldlist()  # FieldList
    fl2 = ds2.to_fieldlist()  # FieldList
    fl = ekd.concat(fl1, fl2)  # FieldList

    len(fl) == len(fl1) + len(fl2)  # True

A :class:`~earthkit.data.core.field.Field` and a ``FieldList`` can also be mixed together; the result is
still a ``FieldList``, with the field prepended to it:

.. code-block:: python

    fl1[0]  # Field
    fl = ekd.concat(fl1[0], fl2)  # FieldList

It can also combine objects that have no underlying source at all, such as ones created with
:func:`~earthkit.data.from_object`. Here ``d1`` and ``d2`` are ``Data`` objects wrapping an
``xarray.Dataset`` (each an :class:`~earthkit.data.data.wrappers.xarray.XarrayDatasetData`), with no
``FieldList``/``Source`` to fall back on, so the result ``d`` is a
:py:class:`~earthkit.data.data.multi.MultiData`. Calling ``to_xarray()`` on it converts it back to a
single ``xarray.Dataset``:

.. code-block:: python

    import xarray as xr

    d1 = ekd.from_object(xr.open_dataset("a.nc"))  # Data object (XarrayDatasetData)
    d2 = ekd.from_object(xr.open_dataset("b.nc"))  # Data object (XarrayDatasetData)

    d = ekd.concat(d1, d2)  # MultiData
    ds = d.to_xarray()  # xarray.Dataset

Whatever the input types, ``concat`` picks the highest level of abstraction it can for the result --
see :ref:`concat-resolution-order` for exactly how. With a single argument, it simply returns it
unchanged.


.. _concat-resolution-order:

How the result type is chosen
--------------------------------

With more than one argument, ``concat`` tries, in order, three decreasing levels of abstraction, and
returns the result of the first attempt that succeeds:

1. **As a fieldlist.** If every argument is a :class:`~earthkit.data.core.field.Field` or a
   :class:`~earthkit.data.core.fieldlist.FieldList`, they are merged via the :ref:`data-sources-multi`
   source and the resulting :class:`~earthkit.data.core.fieldlist.FieldList` is returned.

2. **As a source, or a Data object wrapping one.** Otherwise, if every argument is itself a
   :class:`~earthkit.data.sources.Source`, or a :py:class:`Data <earthkit.data.data.Data>` object whose
   underlying ``_source`` is one, those sources are combined via the :ref:`data-sources-multi` source (so
   the ``merger`` machinery in :ref:`mergers` applies here too, with its default, automatic behaviour).

   The result is unwrapped to a plain ``Source`` only if *every* argument was already a plain ``Source``;
   as soon as at least one argument is a ``Data`` object, the combined result stays a ``Data`` object --
   ``concat`` never discards a higher level of abstraction present among its arguments.

3. **As Data objects.** Otherwise -- typically because at least one argument has no underlying source at
   all, e.g. one created with :func:`~earthkit.data.from_object` -- every argument that is not already a
   :py:class:`Data <earthkit.data.data.Data>` object is converted with its own ``to_data_object()``, and
   the results are combined directly into a :py:class:`~earthkit.data.data.multi.MultiData`. This step
   always succeeds, so it is the final fallback.

Because each attempt is tried against *all* the arguments together, mixing types across the levels above
falls back to the lowest common one: concatenating a ``FieldList`` with a plain ``Source`` skips step 1
(the ``Source`` is not a ``Field``/``FieldList``) and is handled by step 2 instead; concatenating a
``Source`` with an object that has no source at all skips both step 1 and step 2 and falls back to step 3.
