.. _time_component:

Time component
==============

Every :py:class:`~earthkit.data.core.field.Field` carries a *time component* that describes the
temporal coordinate of the field. The time component is accessible via the :attr:`time` attribute
of a field and is represented by a subclass of
:py:class:`~earthkit.data.field.component.time.TimeBase`.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> field = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
    >>> field.time.base_datetime()
    datetime.datetime(2020, 1, 1, 0, 0)
    >>> field.time.step()
    datetime.timedelta(0)
    >>> field.time.valid_datetime()
    datetime.datetime(2020, 1, 1, 0, 0)

The same information is available through the generic :meth:`~earthkit.data.core.field.Field.get`
interface using the ``"time."`` prefix:

.. code-block:: python

    >>> field.get("time.base_datetime")
    datetime.datetime(2020, 1, 1, 0, 0)
    >>> field.get("time.step")
    datetime.timedelta(0)

The time component is **immutable**. Use the
:meth:`~earthkit.data.field.component.time.TimeBase.set` method (or
:meth:`~earthkit.data.core.field.Field.set` on the field) to derive a modified copy:

.. code-block:: python

    >>> new_field = field.set({"time.step": 6})
    >>> new_field.time.step()
    datetime.timedelta(seconds=21600)


Time types
----------

The appropriate time subclass is determined automatically from the data:

- :py:class:`~earthkit.data.field.component.time.ForecastTime` — standard forecast time
  defined by a base datetime and a forecast step. The valid datetime is computed as
  ``base_datetime + step``.
- :py:class:`~earthkit.data.field.component.time.MonthlyForecastTime` — monthly forecast time
  that also carries a ``forecast_month`` value.


Accessing time information
--------------------------

All time keys are accessible through :meth:`~earthkit.data.core.field.Field.get` with the
``"time."`` prefix, and can therefore be used in
:meth:`~earthkit.data.core.fieldlist.FieldList.sel`,
:meth:`~earthkit.data.core.fieldlist.FieldList.order_by`, and
:meth:`~earthkit.data.core.fieldlist.FieldList.metadata`.

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Key
     - Description
   * - ``time.base_datetime``
     - The base (reference) datetime of the forecast as a :py:class:`datetime.datetime`.
   * - ``time.forecast_reference_time``
     - Alias of ``time.base_datetime``.
   * - ``time.base_date``
     - The date part of the base datetime as a :py:class:`datetime.date`.
   * - ``time.base_time``
     - The time-of-day part of the base datetime as a :py:class:`datetime.time`.
   * - ``time.valid_datetime``
     - The valid datetime (``base_datetime + step``) as a :py:class:`datetime.datetime`.
   * - ``time.step``
     - The forecast step as a :py:class:`datetime.timedelta`. Integer values are interpreted as hours.
   * - ``time.forecast_period``
     - Alias of ``time.step``.
   * - ``time.forecast_month``
     - The forecast month as an integer. Only available for monthly forecast time; returns ``None`` otherwise.
   * - ``time.indexing_datetime``
     - The indexing datetime used for ordering within a dataset. Returns ``None`` for types that do not define it.


How-tos
-------

- :ref:`/tutorials/field/field_overview.ipynb`
- :ref:`/tutorials/grib/grib_overview.ipynb`
- :ref:`/tutorials/grib/grib_time_series.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_temporal.ipynb`
- :ref:`/tutorials/xr_engine/xarray_engine_step_ranges.ipynb`
