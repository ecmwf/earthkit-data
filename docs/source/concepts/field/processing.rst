.. _processing_component:

Processing component and metadata keys
======================================

.. warning::

  This component is experimental and may be changed in future versions of earthkit-data.

Every :py:class:`~earthkit.data.core.field.Field` may carry a *processing component*
(``processing``) that describes the processing that produced the field: time statistics
(accumulations, min/max/mean over a window), ensemble statistics (ensemble mean, spread,
...), ensemble probabilities, etc., as well as any ordered sequence of such processing
steps (e.g. the ensemble mean of a 6-hour maximum). The goal is to expose this information
in a uniform, queryable and format-agnostic way so it can be inspected, filtered on and
round-tripped independently of the underlying format (GRIB, CF-netCDF, ...).

The component is accessible via the :attr:`processing` attribute of a field and is
represented by :py:class:`~earthkit.data.field.component.processing.Processing`. Fields
that carry no processing information have an empty component (length 0).

Data model
----------

A :py:class:`~earthkit.data.field.component.processing.Processing` component is an
ordered sequence of :py:class:`~earthkit.data.field.component.processing.ProcessingStep`
objects. The steps appear in the **reversed order of their application**: the outermost
operation (last applied) is first on the list and the innermost operation (first applied)
is last on the list.

The concrete processing steps are:

- :py:class:`~earthkit.data.field.component.processing.ReductionStep` -- a statistical
  ``method`` applied to a sample of size ``sample_size`` along ``axis``, collapsing that axis.
- :py:class:`~earthkit.data.field.component.processing.TimeAggregationStep` -- a statistical
  ``method`` applied to a time window with a given ``window_length``, ``window_anchor`` and
  ``sampling_frequency`` along a time ``axis`` (``forecast_reference_time`` or ``forecast_period``).
- :py:class:`~earthkit.data.field.component.processing.LaggedForecastsAggregationStep` -- an
  aggregation over lagged forecasts.
- :py:class:`~earthkit.data.field.component.processing.EnsembleProbabilityStep` -- the probability
  that a field value falls into ``threshold_interval`` (in ``threshold_interval_units``) based on
  an ensemble of size ``sample_size``.

Durations (e.g. ``window_length``, ``sampling_frequency``) are represented as ISO 8601 durations
by a :py:class:`~earthkit.data.field.component.processing.Duration` object (e.g. ``"PT6H"``,
``"P1M"``, ``"P30Y"``).

Sequence API
------------

The processing component behaves like an immutable sequence of steps:

.. code-block:: python

    len(p)            # number of processing steps
    for ps in p: ...  # iterate over the ProcessingStep objects
    p[i]              # the i-th ProcessingStep
    p[i:j]            # a slice, itself a Processing
    p + other         # concatenation, resulting in a new Processing

Indexing past the end returns an empty processing step whose accessors all return ``None``,
so ``p[999].method()`` is always safe.

Each step exposes one accessor per attribute; inapplicable ones return ``None``:

.. code-block:: python

    >>> ps = p[0]
    >>> ps.kind()
    'time_aggregation'
    >>> ps.axis()
    'forecast_period'
    >>> ps.method()
    'maximum'
    >>> ps.window_length()            # ISO 8601 string by default
    'PT6H'
    >>> ps.window_length(type=datetime.timedelta)
    datetime.timedelta(seconds=21600)
    >>> ps.sample_size()              # not applicable to this step
    None

The component also offers propagated accessors that return a tuple with one value per
processing step (``None`` where not applicable):

.. code-block:: python

    >>> p.kind()
    ('time_aggregation', 'reduction')
    >>> p.method()
    ('maximum', 'mean')
    >>> p.window_length()
    ('PT6H', None)
    >>> p.sample_size()
    (None, 50)

Keyed access mirrors the other field components. A plain key returns the propagated tuple;
an indexed key ``"<attr>[i]"`` returns a single step's value (exactly ``p[i].get("<attr>")``):

.. code-block:: python

    >>> p.get("method")
    ('maximum', 'mean')
    >>> p.get("method[0]")
    'maximum'
    >>> p.get("sample_size[1]")
    50

The ``set`` method returns a new processing component (the original is untouched):

.. code-block:: python

    >>> p.set({"method[0]": "mean"})     # tweak one attribute of step 0
    >>> p[0].set(method="mean")          # the step-level equivalent
    >>> p.set([{...}, {...}])            # replace the whole chain

Serialisation is symmetric and format-neutral:

.. code-block:: python

    >>> p.to_dict()
    {'items': [{...}, {...}]}
    >>> Processing.from_dict(d)           # rebuild from a dict (or a list of item dicts)

Field access
------------

``field.processing`` is the component; ``field.get()`` / ``field.set()`` delegate to it
under the ``"processing."`` prefix. The index may sit on the sub-key or on the component name:

.. code-block:: python

    >>> field.processing                        # the Processing component
    >>> field.get("processing.method")          # ('maximum', 'mean') -- whole chain
    >>> field.get("processing.method[0]")       # 'maximum'          -- outermost step
    >>> field.get("processing[0].method")       # 'maximum'          -- same thing
    >>> field2 = field.set({"processing.method[0]": "mean",
    ...                     "processing[0].window_length": "P1M"})

Field list filtering
--------------------

An indexed processing key pins the match to a specific position in the processing chain:

.. code-block:: python

    # the OUTERMOST step is an ensemble mean
    fl.sel({"processing.axis[0]": "ensemble", "processing.method[0]": "mean"})

A plain (unindexed) processing key is chain-valued and matches if **any** step in the
field's chain matches -- with either a single value or a list of values:

.. code-block:: python

    # any step is a 6-hourly window (matches "monthly mean of 6h max" too)
    fl.sel({"processing.window_length": "PT6H"})
    fl.sel({"processing.window_length": ["PT6H", "PT12H", "P1D"]})

Duration comparison is fuzzy about calendar components: a month spans 28-31 days and a year
360-366 days, so ``"P1M"`` matches any of ``"P28D"`` .. ``"P31D"`` and ``"P1Y"`` matches any of
``"P360D"`` .. ``"P366D"``. A slice selects a closed interval (inclusive of both bounds):

.. code-block:: python

    # any step's window is between 6 hours and 1 day (inclusive)
    fl.sel({"processing.window_length": slice("PT6H", "P1D")})
    # open-ended: window at least 6-hourly
    fl.sel({"processing.window_length": slice("PT6H", None)})


Tutorials / How-tos
-------------------

- :ref:`/tutorials/field/field_overview.ipynb`
- :ref:`/tutorials/grib/grib_overview.ipynb`
