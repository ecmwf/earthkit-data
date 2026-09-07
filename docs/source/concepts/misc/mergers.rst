.. _mergers:

Merging multiple sources
==========================

When *earthkit-data* reads more than one input at once (e.g. a list of files, or multiple sources
explicitly combined with the ``multi`` source) the result is a single object made up of several
sub-sources. What that combined object actually looks like, and whether it collapses into one single
object of a definite type, is controlled by the **merger** concept described on this page.

.. note::

    As explained in :ref:`data-object`, :func:`from_source` never returns a raw ``Source`` object, it
    always returns a :py:class:`Data <earthkit.data.data.Data>` object. The ``Source``/``MultiSource``
    objects and the mergers described below are the internal machinery that decides *what kind* of
    ``Data`` object comes out the other end -- see :ref:`mergers-and-data-objects` for how the two relate.

The merger concept
--------------------

Whenever *earthkit-data* ends up with more than one source to represent as one object, it wraps them
internally in a :class:`~earthkit.data.sources.multi.MultiSource`. A ``MultiSource`` behaves like the
concatenation of its sub-sources (e.g. iterating over it yields the items of each sub-source in turn), but
on its own it does not know how to combine them into, say, a single :ref:`fieldlist <fieldlist_concept>`,
an ``xarray.Dataset`` or a ``pandas.DataFrame``. That is the job of a **merger**.

A merger is an object that knows how to turn a list of sources into a single result of a given target
type. It is only invoked lazily, when one of the conversion methods is actually called:

- :func:`~earthkit.data.sources.multi.MultiSource.to_fieldlist`
- :func:`~earthkit.data.sources.multi.MultiSource.to_xarray`
- :func:`~earthkit.data.sources.multi.MultiSource.to_pandas`

Which merger is used is controlled by the ``merger`` keyword argument, accepted wherever a
``MultiSource`` can be created — most notably in the :ref:`data-sources-multi` source, but also
transparently whenever the :ref:`data-sources-file` source (or any other source accepting multiple inputs)
is given more than one input, see :ref:`mergers-multi-file` below.

``merger`` can take the following values. The examples below assume ``d1`` and ``d2`` are
:py:class:`Data <earthkit.data.data.Data>` objects, e.g. each individually obtained with
``ekd.from_source("file", ...)`` -- see :ref:`mergers-and-data-objects` for why this is the right thing to
pass, rather than a raw ``Source``.

``None`` (the default)
    Requests **automatic merging**. As the ``MultiSource`` is created, any sub-source *earthkit-data*
    could not recognise the format of (e.g. an unsupported file type) is silently ignored and dropped from
    the collection -- see ``False`` below for how to keep such sub-sources instead. *earthkit-data*
    then tries to merge the remaining sub-sources by their nearest common class (e.g. when all of them are
    GRIB fieldlists). If that succeeds, the ``MultiSource`` immediately mutates itself into the single
    merged object, so from that point on it behaves exactly as if a single source had been read in the
    first place. If it fails (e.g. because the sub-sources are of unrelated types), no merger is built and
    the object remains a plain collection of its (already filtered) sub-sources, to be merged later,
    lazily, via the ``DefaultMerger`` (see below) when one of the conversion methods is called.

``False``
    **Disables merging** entirely, and additionally causes sources that would otherwise be silently
    dropped when a ``MultiSource`` is created (typically ones *earthkit-data* could not recognise the
    format of, e.g. unsupported file types) to be kept instead. This is useful for inspecting exactly what
    *earthkit-data* found, e.g. via ``ds.path``, without triggering any merge attempt.

    .. note::

        ``merger=False`` is only available from version 1.3 onwards.

A **string**
    Names one of the built-in mergers, optionally with ``key=value`` arguments in parentheses:

    - ``"concat"`` -- concatenate the sub-sources along a dimension using ``xarray.open_mfdataset``. E.g.
      ``"concat(dim=time)"``.
    - ``"merge"`` -- merge the sub-sources by their nearest common class, the same logic as the automatic
      ``None`` case, but reached explicitly rather than as a fallback.

    .. code-block:: python

        import earthkit.data as ekd

        ds = ekd.from_source("multi", [d1, d2], merger="concat(dim=time)")
        ds.to_xarray()

A **tuple**
    An alternative, non-string way to specify one of the builtin mergers above, as ``(name, kwargs_dict)``
    or ``(name, *args)``. Useful when an argument cannot be represented as plain text, e.g.:

    .. code-block:: python

        ds = ekd.from_source("multi", [d1, d2], merger=("concat", {"dim": "time"}))

A **callable**
    A custom merger as a plain function (or any callable), receiving the merged file paths of the
    sub-sources (or the sub-sources themselves, when their paths could not be resolved) as its only
    positional argument, plus any keyword arguments passed to the conversion call:

    .. code-block:: python

        import xarray as xr


        def my_merger(paths_or_sources, **kwargs):
            return xr.open_mfdataset(paths_or_sources, **kwargs)


        ds = ekd.from_source("multi", [d1, d2], merger=my_merger).to_xarray()

An **object**
    A custom merger as an object implementing one or more of ``to_fieldlist``, ``to_xarray`` and
    ``to_pandas``. Only the conversions actually needed have to be implemented. Each method receives the
    same arguments as the callable case above:

    .. code-block:: python

        class MyMerger:
            def to_xarray(self, paths_or_sources, **kwargs):
                return xr.open_mfdataset(paths_or_sources, **kwargs)


        ds = ekd.from_source("multi", [d1, d2], merger=MyMerger()).to_xarray()

.. note::

    Whatever form ``merger`` takes, it is never a ``Merger`` object itself. *earthkit-data* builds the
    actual :class:`~earthkit.data.mergers.Merger` instance internally from whichever of the above was
    supplied.


.. _mergers-and-data-objects:

Mergers and Data objects
---------------------------

:func:`from_source` always returns a :py:class:`Data <earthkit.data.data.Data>` object (see
:ref:`data-object`), never the underlying ``Source``/``MultiSource``. When multiple sources are combined
and the input cannot be reduced to a single, type-specific ``Data`` object, :func:`from_source` returns a
:py:class:`~earthkit.data.data.multi.MultiData` object instead. ``MultiData`` wraps the underlying
``MultiSource`` and forwards its own ``to_fieldlist``/``to_xarray``/``to_pandas`` calls to it, which is
where the merger machinery described above actually runs.

Conversely, when automatic merging (``merger=None``, the default) succeeds -- e.g. all the inputs are
GRIB -- the ``MultiSource`` mutates itself into a single merged source before :func:`from_source` returns,
so a single, type-specific ``Data`` object (e.g. ``GribData``) comes back instead of a ``MultiData``, and
the multi-source nature of the input becomes invisible to the caller.

.. code-block:: python

    import earthkit.data as ekd

    ds = ekd.from_source("file", ["a.grib", "b.grib"])
    type(ds).__name__  # "GribData": automatic merging succeeded

    ds = ekd.from_source("file", ["a.grib", "b.nc"])
    type(ds).__name__  # "MultiData": mixed types, returns a MultiData

A ``Data`` object such as the one returned by :func:`from_source` can itself be passed back into another
``from_source`` call as one of the sources to combine -- ``MultiSource`` recognises it and unwraps its
underlying ``Source`` automatically.

Using mergers with multiple sources
--------------------------------------

The ``merger`` kwarg can be passed to any source that ends up combining several sub-sources, most directly
the :ref:`data-sources-multi` source, which explicitly combines a list of already created data objects:

.. code-block:: python

    import earthkit.data as ekd

    d1 = ekd.from_source("file", "a.grib")
    d2 = ekd.from_source("file", "b.grib")

    ds = ekd.from_source("multi", [d1, d2], merger="concat(dim=time)")

Nested ``multi`` sources are flattened before merging, unless a nested ``MultiSource`` has its own,
explicit merger, in which case it is merged separately using it and treated as a single unit by the outer
merger.


.. _mergers-multi-file:

Multiple input files in the file source
------------------------------------------

The most common way to end up with a merger in practice is not by using ``multi`` directly, but simply by
giving the :ref:`data-sources-file` source a list of paths instead of a single one:

.. code-block:: python

    import earthkit.data as ekd

    ds = ekd.from_source("file", ["a.grib", "b.grib", "c.grib"])

Internally, when more than one path is given, the ``file`` source builds a ``multi`` source out of the
individual per-file sources, and the ``merger`` kwarg is simply forwarded to it:

.. code-block:: python

    # equivalent to the multi-path from_source call above
    ds = ekd.from_source(
        "multi",
        [
            ekd.from_source("file", "a.grib"),
            ekd.from_source("file", "b.grib"),
            ekd.from_source("file", "c.grib"),
        ],
    )

This means the same ``merger`` values described above can be passed directly to ``from_source("file", ...)``
when reading multiple files:

.. code-block:: python

    # automatic merging (default): if all files are e.g. GRIB, ds is a single, type-specific
    # Data object (GribData), exactly as if a single file had been read
    ds = ekd.from_source("file", ["a.grib", "b.grib"])

    # disable merging, keep every file as a separate, individually accessible source;
    # ds is a MultiData object
    ds = ekd.from_source("file", ["a.grib", "unsupported.bin"], merger=False)
    print(ds.path)  # ["<path>/a.grib", "<path>/unsupported.bin"]

    # concatenate NetCDF files along a dimension
    ds = ekd.from_source("file", ["a.nc", "b.nc"], merger="concat(dim=time)")
    ds.to_xarray()

As with ``multi``, when ``merger`` is left as ``None`` (the default) and the per-file sources all resolve
to the same class (e.g. they are all recognised as GRIB), the underlying sources merge into one straight
away and :func:`from_source` returns a single, type-specific ``Data`` object rather than a ``MultiData``
(see :ref:`mergers-and-data-objects`), so the multi-file nature of the input becomes invisible to the rest
of the code.
