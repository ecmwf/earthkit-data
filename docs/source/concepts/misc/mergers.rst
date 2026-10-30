.. _mergers:

Merging multiple sources
==========================

When *earthkit-data* reads more than one input at once (e.g. a list of files, or multiple sources
explicitly combined with the :ref:`data-sources-multi` source), it combines them into a single object. What that combined object actually looks like, and whether it collapses into one single
object of a definite type, is controlled by the **merger** concept described on this page.

.. note::

    As explained in :ref:`data-object`, :func:`from_source` never returns a raw ``Source`` object, it
    always returns a :py:class:`Data <earthkit.data.data.Data>` object. The ``Source``/``MultiSource``
    objects and the mergers described below are the internal machinery that decides *what kind* of
    ``Data`` object comes out the other end.

.. note::

    To combine two or more Data objects, use :func:`~earthkit.data.utils.concat.concat`
    -- see :ref:`concat`. Note that the ``merger`` keyword is not yet supported there.


.. _mergers-details:

The merger concept
--------------------

Whenever *earthkit-data* ends up with more than one source to represent as one object, it wraps them
internally in a :class:`~earthkit.data.sources.multi.MultiSource`. How these sub-sources are combined into
a single result is determined by the ``merger`` keyword argument, which can be set in the
:ref:`data-sources-multi` source, but also transparently in the :ref:`data-sources-file` source (or any
other source accepting multiple inputs).

``merger`` can take the following values.

``None`` (the default)
    Requests **automatic merging**. As the ``MultiSource`` is created, any item *earthkit-data*
    could not recognise the format of (e.g. an unsupported file type) is silently dropped from
    the collection -- see ``False`` below for how to keep such items instead. *earthkit-data*
    then tries to merge the remaining items by their nearest common class (e.g. when all of them are
    GRIB fieldlists). If that succeeds, the corresponding ``Data`` object is created directly. Otherwise,
    the result is a ``MultiData`` object, and the merging is deferred until one of the conversion methods
    is called, at which point it is attempted lazily using the built-in :ref:`DefaultMerger
    <mergers-default-merger>`.

``False``
    **Disables merging** entirely, and additionally causes sources that would otherwise be silently
    dropped when a ``MultiSource`` is created (typically ones *earthkit-data* could not recognise the
    format of, e.g. unsupported file types) to be kept instead. This is useful for inspecting exactly what
    *earthkit-data* found, e.g. via ``ds.path``, without triggering any merge attempt.

    .. note::

        ``merger=False`` is only available from version 1.3 onwards.

Any other value for the ``merger`` keyword argument specifies a custom merger, provided as a string, tuple,
or callable, as described in the sections below. As with automatic merging, unrecognised items are dropped
as the ``MultiSource`` is created, but no immediate merge attempt is made: the result is always a
``MultiData`` object, and the specified ``merger`` is applied lazily once one of the conversion methods is
called.

The following sections describe the different ways to specify a custom merger.

A **string**
    Names one of the built-in mergers, optionally with ``key=value`` arguments in parentheses:

    - ``"concat"`` -- concatenate the sub-sources along a dimension using ``xarray.open_mfdataset``. E.g.
      ``"concat(dim=time)"``.
    - ``"merge"`` -- merge the sub-sources by their nearest common class, the same logic as the automatic
      ``None`` case, but reached explicitly rather than as a fallback.

    .. code-block:: python

        import earthkit.data as ekd

        d1 = ekd.from_source("file", "a.nc")
        d2 = ekd.from_source("file", "b.nc")
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



.. _mergers-class:

Mergers
-----------

Internally, mergers are represented by a ``Merger``, a class
providing the ``to_fieldlist``, ``to_xarray`` and ``to_pandas`` conversion
methods for multiple items. A given ``Merger`` only needs to implement the conversions it actually supports.


.. _mergers-default-merger:

The DefaultMerger
------------------------------------------

:py:class:`DefaultMerger <earthkit.data.mergers.DefaultMerger>` is the merger used whenever no explicit
``merger`` is requested (``merger=None``). It
builds its result by converting each item on its own and then combining those individual results. Each of
its three conversion methods does this differently:

``to_fieldlist()``
    Turns each item into its own fieldlist -- a ``Field`` via its own ``to_fieldlist()``, a ``FieldList``
    used as is, a file path read with :func:`from_source`, or (for anything else, e.g. a ``Data`` object)
    by calling its own ``to_fieldlist()`` -- then merges the resulting fieldlists using the ``merge``
    classmethod of their nearest common class (the same logic automatic merging uses, see
    :ref:`mergers`).

``to_pandas()``
    Calls ``to_pandas()`` on each item individually, then concatenates the resulting ``DataFrame`` objects
    with ``pandas.concat`` (``ignore_index=True`` by default).

``to_xarray()``
    Resolves the file path of each item, if possible for all of them, and opens the collection with a
    single ``xarray.open_mfdataset(paths)`` call. If paths cannot be resolved for every item, the items
    themselves are opened directly instead, one by one, through an internal xarray backend.


.. _mergers-file-source:

Usage with the file source
------------------------------------------

The same ``merger`` values described above can also be passed directly to ``from_source("file", ...)``
when reading multiple files, since the ``file`` source builds a ``multi`` source internally and forwards
``merger`` to it:

.. code-block:: python

    # automatic merging (default): if all files are e.g. GRIB, ds is a single, type-specific
    # Data object (GribData), exactly as if a single file had been read
    ds = ekd.from_source("file", ["a.grib", "b.grib"])

    # disable merging, keep every file as a separate, individually accessible source;
    # ds is a MultiData object
    ds = ekd.from_source("file", ["a.grib", "unsupported.bin"], merger=False)
    print(ds.path)  # ["<path>/a.grib", "<path>/unsupported.bin"]

    # concatenate NetCDF files along a dimension using a custom merger
    # ds is a MultiData object
    ds = ekd.from_source("file", ["a.nc", "b.nc"], merger="concat(dim=time)")
    # the custom merger will be used in the call to ``to_xarray()``
    ds.to_xarray()
