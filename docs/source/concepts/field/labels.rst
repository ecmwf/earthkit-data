.. _labels_component:

Labels component
================

Every :py:class:`~earthkit.data.core.field.Field` carries a *labels component* that stores
arbitrary user-defined key-value pairs attached to the field. Unlike the other components
(parameter, time, vertical, …), labels are not populated automatically from the source data;
they are a blank slate that the user can fill with any information they find useful.

The labels component is accessible via the :attr:`labels` attribute of a field and is
represented by a :py:class:`~earthkit.data.field.handler.labels.SimpleLabels` object.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> f = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
    >>> f.labels
    {}

By default the labels are empty. Values are added by calling
:meth:`~earthkit.data.core.field.Field.set` with ``"labels.<key>"`` keys:

.. code-block:: python

    >>> f1 = f.set({"labels.source": "reanalysis", "labels.experiment": 42})
    >>> f1.labels
    {'source': 'reanalysis', 'experiment': 42}
    >>> f1.labels["source"]
    'reanalysis'
    >>> f1.labels.get("experiment")
    42
    >>> f1.get("labels.experiment")
    42


Labels and immutability
-----------------------

Labels are **immutable**: once a
:py:class:`~earthkit.data.field.handler.labels.SimpleLabels` object is created, its
entries cannot be modified in place. Use
:meth:`~earthkit.data.field.handler.labels.SimpleLabels.set` on the labels object (or
:meth:`~earthkit.data.core.field.Field.set` on the field) to obtain a new object with
the requested changes:

.. code-block:: python

    >>> # update an existing label or add a new one
    >>> f2 = f1.set({"labels.experiment": 99})
    >>> f2.labels
    {'source': 'reanalysis', 'experiment': 99}

    >>> # original field is unchanged
    >>> f1.labels
    {'source': 'reanalysis', 'experiment': 42}

Multiple :meth:`~earthkit.data.core.field.Field.set` calls **accumulate** label entries
rather than replacing the whole labels object:

.. code-block:: python

    >>> f3 = f1.set({"labels.run": "ctrl"})
    >>> f3.labels
    {'source': 'reanalysis', 'experiment': 42, 'run': 'ctrl'}


Removing labels
---------------

Use :meth:`~earthkit.data.field.handler.labels.SimpleLabels.remove` to drop one or more
keys and then pass the result back to :meth:`~earthkit.data.core.field.Field.set`:

.. code-block:: python

    >>> new_labels = f3.labels.remove("run")
    >>> f4 = f3.set(labels=new_labels)
    >>> f4.labels
    {'source': 'reanalysis', 'experiment': 42}

    >>> # remove multiple keys at once
    >>> new_labels = f3.labels.remove("source", "run")
    >>> f5 = f3.set(labels=new_labels)
    >>> f5.labels
    {'experiment': 42}


Querying labels
---------------

Labels support the standard dictionary interface:

.. code-block:: python

    >>> f3.labels["source"]
    'reanalysis'
    >>> f3.labels.get("missing_key", "default")
    'default'
    >>> f3.labels.get("experiment", astype=str)
    '42'
    >>> "source" in f3.labels
    True
    >>> len(f3.labels)
    3
    >>> list(f3.labels.keys())
    ['source', 'experiment', 'run']
    >>> list(f3.labels.items())
    [('source', 'reanalysis'), ('experiment', 42), ('run', 'ctrl')]

The generic :meth:`~earthkit.data.core.field.Field.get` method also supports the
``"labels.<key>"`` prefix:

.. code-block:: python

    >>> f3.get("labels.source")
    'reanalysis'

This means label keys can be used in
:meth:`~earthkit.data.core.fieldlist.FieldList.sel`,
:meth:`~earthkit.data.core.fieldlist.FieldList.order_by`, and
:meth:`~earthkit.data.core.fieldlist.FieldList.metadata` just like any other component
key:

.. code-block:: python

    >>> fl = some_fieldlist.sel(**{"labels.source": "reanalysis"})
    >>> fl = some_fieldlist.order_by("labels.experiment")


Labels and GRIB data
--------------------

When a field originates from a GRIB message, setting only labels (without touching any
core component key) keeps the raw GRIB metadata intact. The underlying GRIB message is
still accessible via :meth:`~earthkit.data.core.field.Field.message` and ecCodes keys
can still be read through :meth:`~earthkit.data.core.field.Field.get` using the
``"metadata."`` prefix:

.. code-block:: python

    >>> f1 = f.set({"labels.my_label": "val"})
    >>> f1.get("labels.my_label")
    'val'
    >>> f1.get("metadata.shortName")   # raw GRIB key still accessible
    '2t'


SimpleLabels API summary
------------------------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Method / attribute
     - Description
   * - ``labels["key"]``
     - Return the value for *key*; raises :py:exc:`KeyError` if absent.
   * - ``labels.get(key, default=None, *, astype=None, raise_on_missing=False)``
     - Return the value for *key*, optionally cast to *astype*. Returns *default* when
       absent (or raises :py:exc:`KeyError` when ``raise_on_missing=True``).
   * - ``"key" in labels``
     - ``True`` if *key* exists.
   * - ``len(labels)``
     - Number of label entries.
   * - ``labels.keys()``
     - Iterable of all label keys.
   * - ``labels.items()``
     - Iterable of ``(key, value)`` pairs.
   * - ``labels.set(**kwargs)``
     - Return a new :py:class:`~earthkit.data.field.handler.labels.SimpleLabels` with the
       given keys added or overwritten. The original object is unchanged.
   * - ``labels.remove(*keys)``
     - Return a new :py:class:`~earthkit.data.field.handler.labels.SimpleLabels` with the
       specified keys removed. The original object is unchanged. Raises
       :py:exc:`KeyError` if a key does not exist.
   * - ``labels.to_dict()``
     - Return a plain :py:class:`dict` copy of all label entries.


Tutorials / How-tos
-------------------

- :ref:`/tutorials/field/field_labels.ipynb`
- :ref:`/tutorials/field/field_overview.ipynb`
