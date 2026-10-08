Selecting data with sel
=======================

``earthkit sel`` selects GRIB fields, BUFR messages or NetCDF coordinate labels
and writes the result to a target file.

Syntax
------

.. code-block:: bash

   earthkit sel SOURCE_FILE TARGET_FILE KEY=VALUE [KEY=VALUE ...]

At least one condition is required. Conditions on different keys are combined
with logical AND. Each key may appear only once. Quote arguments containing
spaces so the shell passes each condition as a single argument.

Selection values
----------------

* A scalar such as ``700`` or ``t`` selects that value.
* Comma-separated values specify alternatives: ``1,4`` selects 1 or 4.
* Integer ranges have an exclusive stop: ``1:4`` selects 1, 2 and 3.
* An optional non-zero integer step is supported: ``1:6:2`` selects 1, 3 and 5,
  while ``4:1:-1`` selects 4, 3 and 2.
* An open lower bound such as ``:4`` selects values below 4. An open upper
  bound such as ``4:`` selects values greater than or equal to 4.

Bounded ranges may be combined with list values, for example ``1:4,6``.
Open-ended ranges cannot be combined with lists or use a step. A bare ``:``
is not supported. List items and scalar values must not be empty.

.. important::

   CLI ranges exclude the stop value. This differs from slices passed directly
   to :meth:`earthkit.data.core.fieldlist.FieldList.sel`, which include both
   bounds. For example, the CLI equivalent of ``slice(500, 700)`` for integer
   levels is ``500:701``.

GRIB
----

GRIB input is converted to a FieldList and selected using
:meth:`earthkit.data.core.fieldlist.FieldList.sel`. Conditions use the metadata
keys accepted by that method, including component keys and raw metadata keys.

.. code-block:: bash

   earthkit sel input.grib selected.grib parameter.variable=t
   earthkit sel input.grib selected.grib parameter.variable=t,u vertical.level=500,700
   earthkit sel input.grib selected.grib metadata.paramId=131 vertical.level=500:701
   earthkit sel input.grib selected.grib vertical.level=700:

Date and forecast-step conditions use the normalisation provided by the Python
selection API. Valid ISO datetime strings are preserved even though they contain
colons:

.. code-block:: bash

   earthkit sel input.grib selected.grib time.valid_datetime=2020-12-21T21:00:00
   earthkit sel input.grib selected.grib parameter.variable=t time.step=3,6

Selection preserves the source field order; use :doc:`order_by` to change it.

BUFR
----

BUFR input is converted to a FeatureList. Selection uses message header metadata
such as ``dataCategory`` and ``ident``; it does not filter observations within
individual messages. String values retain leading zeroes.

.. code-block:: bash

   earthkit sel input.bufr selected.bufr dataCategory=2
   earthkit sel input.bufr selected.bufr dataCategory=2 ident=01400,11747
   earthkit sel input.bufr selected.bufr dataCategory=:3

NetCDF
------

NetCDF input is converted to an xarray Dataset, not a FieldList. Selection calls
``Dataset.sel`` with native coordinate names such as ``level`` and ``latitude``.
FieldList metadata keys such as ``vertical.level`` are not used for NetCDF.

.. code-block:: bash

   earthkit sel input.nc selected.nc level=700
   earthkit sel input.nc selected.nc level=300:500 latitude=0,30
   earthkit sel input.nc selected.nc level=700:

Lists and ranges are matched against the labels present in each coordinate,
retaining their source order. Absent labels in a list or range are ignored;
a missing scalar label raises an error. Scalar selection follows xarray's
behaviour and can remove the selected dimension. These conditions select
coordinate labels, not data variable names.

Limitations
-----------

The CLI accepts scalar values, lists and integer ranges. Python-only selection
arguments such as remapping dictionaries and custom callable filters are not
exposed. For GRIB or BUFR, no matches can result in an empty output or no target
file being created.
