.. _ensemble_component:

Ensemble component and metadata keys
======================================

Every :py:class:`~earthkit.data.core.field.Field` may carry an *ensemble component* that
identifies which ensemble member the field belongs to. The ensemble component is accessible
via the :attr:`ensemble` attribute of a field and is represented by a subclass of
:py:class:`~earthkit.data.field.component.ensemble.EnsembleBase`.

Fields from deterministic (non-ensemble) data have an
:py:class:`~earthkit.data.field.component.ensemble.EmptyEnsemble` component where
:meth:`~earthkit.data.field.component.ensemble.EnsembleBase.member` returns ``None``.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> field = ekd.from_source("sample", "ens_cf_pf.grib").to_fieldlist()[2]
    >>> field.ensemble.member()
    '1'
    >>> field.get("ensemble.member")
    '1'

The ensemble component is **immutable**. Use the
:meth:`~earthkit.data.field.component.ensemble.EnsembleBase.set` method (or
:meth:`~earthkit.data.core.field.Field.set` on the field) to derive a modified copy:

.. code-block:: python

    >>> new_field = field.set({"ensemble.member": "5"})
    >>> new_field.ensemble.member()
    '5'


Member representation
---------------------

The member value is stored internally as a string. Integer values passed during construction
or via :meth:`set` are converted automatically. ``None`` represents the absence of an
ensemble member (deterministic data).


List of ensemble metadata keys
-------------------------------

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Key
     - Description
   * - ``ensemble.member``
     - Ensemble member identifier as a string, or ``None`` for deterministic data.
   * - ``ensemble.realization``
     - Alias of ``ensemble.member``.
   * - ``ensemble.realisation``
     - Alias of ``ensemble.member``.


Tutorials / How-tos
-------------------

- :ref:`/tutorials/field/field_overview.ipynb`
- :ref:`/tutorials/grib/grib_overview.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_ensemble.ipynb`
