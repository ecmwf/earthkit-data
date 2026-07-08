.. _proc_component:

Processing (proc) component
============================

.. warning::

  This component is experimental and may be changed in future versions of earthkit-data.

Every :py:class:`~earthkit.data.core.field.Field` may carry a *processing component* (``proc``)
that describes post-processing operations applied to produce the field. The processing component
is accessible via the :attr:`proc` attribute of a field and is represented by a subclass of
:py:class:`~earthkit.data.field.component.proc.ProcBase`.

Fields that carry no processing information have an
:py:class:`~earthkit.data.field.component.proc.EmptyProc` component where all keys
return ``None``.

.. note::

    The ``proc`` component interface is still under active development. Its final form
    is not yet fully defined, and breaking changes may occur in future releases.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> field = ekd.from_source("file", "lsp_step_range.grib2").to_fieldlist()[0]
    >>> field.proc.time_method()
    accum
    >>> field.proc.time_value()
    datetime.timedelta(seconds=259200)
    >>> field.get("proc.time_method")
    accum


Processing items
----------------

The processing component stores a list of
:py:class:`~earthkit.data.field.component.proc.ProcItem` instances. Currently the only
supported item type is
:py:class:`~earthkit.data.field.component.proc.TimeProcItem`, which pairs a time-span value
with a processing method.

Time processing methods
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Enum member
     - Name string
     - Description
   * - ``TimeMethods.ACCUMULATED``
     - ``"accum"``
     - Field values represent an accumulation over the time span (e.g. precipitation totals).
   * - ``TimeMethods.AVERAGE``
     - ``"avg"``
     - Field values represent a time average over the time span.
   * - ``TimeMethods.INSTANT``
     - ``"instant"``
     - Field values are instantaneous (no time averaging or accumulation).
   * - ``TimeMethods.MAX``
     - ``"max"``
     - Field values represent the maximum over the time span.


Accessing processing information
---------------------------------

All proc keys are accessible through :meth:`~earthkit.data.core.field.Field.get` with the
``"proc."`` prefix, and can therefore be used in
:meth:`~earthkit.data.core.fieldlist.FieldList.sel`,
:meth:`~earthkit.data.core.fieldlist.FieldList.order_by`, and
:meth:`~earthkit.data.core.fieldlist.FieldList.metadata`.

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Key
     - Description
   * - ``proc.time``
     - The first :py:class:`~earthkit.data.field.component.proc.TimeProcItem` in the processing
       list, or ``None`` if no time processing is present.
   * - ``proc.time_value``
     - The time-span value from the first time processing item as a :py:class:`datetime.timedelta`,
       or ``None``.
   * - ``proc.time_method``
     - The processing method from the first time processing item as a
       :py:class:`~earthkit.data.field.component.time_span.TimeMethod`, or ``None``.


Tutorials / How-tos
-------------------

- :ref:`/tutorials/field/field_overview.ipynb`
- :ref:`/tutorials/grib/grib_overview.ipynb`
