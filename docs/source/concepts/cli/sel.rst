Selecting data with sel
=======================

``earthkit sel`` selects GRIB fields, BUFR messages or NetCDF coordinate labels
and writes the result to a target.

Syntax
------

.. code-block:: bash

   earthkit sel SOURCE TARGET --KEY VALUE [--KEY VALUE ...]

See :doc:`index` for the forms of ``SOURCE`` and ``TARGET``. At least one
condition is required, given as ``--KEY VALUE`` or ``--KEY=VALUE``. Conditions on
different keys are combined with logical AND. Each key may appear only once.
Options can be given anywhere on the command line. Quote values containing
spaces or shell characters.

Selection values
----------------

* A scalar such as ``700`` or ``t`` selects that value.
* Comma-separated values specify alternatives: ``1,4`` selects 1 or 4.
* A slice ``START:STOP`` selects the values from START to STOP, both included:
  ``300:500`` selects 300, 400 and 500. Either bound can be left out: ``:500``
  selects values up to 500, ``700:`` values from 700.
* The bounds of a slice are numbers, ISO date-times, or quoted strings:

  .. code-block:: bash

     --vertical.level 10:18                                    # numbers
     --time.valid_datetime '2020-12-21T12:00:2020-12-21T18:00'  # date-times
     --parameter.variable '"t":"u"'                             # strings

  Quoting decides the type: ``'2000:2001'`` compares numbers, while
  ``'"2000":"2001"'`` compares strings.
* An integer slice can have a non-zero STEP: ``300:700:200`` selects 300, 500
  and 700, while ``4:1:-1`` selects 4, 3, 2 and 1.

Integer slices with both bounds may be combined with list values, for example
``1:4,6`` selects 1, 2, 3, 4 and 6. A single ISO date-time such as
``2020-12-21T21:00:00`` is a value, not a slice. A bare ``:`` is not supported,
and list items and scalar values must not be empty.

.. note::

   Slices include their STOP, as slices passed to
   :meth:`earthkit.data.core.fieldlist.FieldList.sel` and ``xarray.Dataset.sel``
   do.

GRIB
----

GRIB input is converted to a FieldList and selected using
:meth:`earthkit.data.core.fieldlist.FieldList.sel`. Conditions use the metadata
keys accepted by that method, including component keys and raw metadata keys.

.. code-block:: bash

   earthkit sel input.grib selected.grib --parameter.variable t
   earthkit sel input.grib selected.grib --parameter.variable t,u --vertical.level 500,700
   earthkit sel input.grib selected.grib --metadata.paramId 131 --vertical.level 500:700
   earthkit sel input.grib selected.grib --vertical.level 700:

Date and forecast-step values use the normalisation provided by the Python
selection API, and slices compare the metadata values directly:

.. code-block:: bash

   earthkit sel input.grib selected.grib --time.valid_datetime 2020-12-21T21:00:00
   earthkit sel input.grib selected.grib --time.valid_datetime '2020-12-21T12:00:2020-12-21T18:00'
   earthkit sel input.grib selected.grib --parameter.variable t --time.step 3,6

Selection preserves the source field order; use :doc:`order_by` to change it.

BUFR
----

BUFR input is converted to a FeatureList. Selection uses message header metadata
such as ``dataCategory`` and ``ident``; it does not filter observations within
individual messages. String values retain leading zeroes.

.. code-block:: bash

   earthkit sel input.bufr selected.bufr --dataCategory 2
   earthkit sel input.bufr selected.bufr --dataCategory 2 --ident 01400,11747
   earthkit sel input.bufr selected.bufr --dataCategory :2

NetCDF
------

NetCDF input is converted to an xarray Dataset, not a FieldList. Selection calls
``Dataset.sel`` with native coordinate names such as ``level`` and ``latitude``.
FieldList metadata keys such as ``vertical.level`` are not used for NetCDF.

.. code-block:: bash

   earthkit sel input.nc selected.nc --level 700
   earthkit sel input.nc selected.nc --level 300:500 --latitude 0,30
   earthkit sel input.nc selected.nc --level 700:

Lists and slices are matched against the labels present in each coordinate,
retaining their source order, so slices also work on decreasing coordinates.
Absent labels in a list or slice are ignored; a missing scalar label raises an
error. Scalar selection follows xarray's behaviour and can remove the selected
dimension. These conditions select coordinate labels, not data variable names.
NetCDF input cannot be read from stdin.

Limitations
-----------

The CLI accepts scalar values, lists and slices. Python-only selection
arguments such as remapping dictionaries and custom callable filters are not
exposed. For GRIB or BUFR, no matches can result in an empty output or no target
file being created.
