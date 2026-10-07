Ordering data with order_by
===========================

``earthkit order_by`` reorders GRIB fields or BUFR messages by metadata and
writes all messages to a target file. NetCDF and other input formats are not
supported.

Syntax
------

.. code-block:: bash

   earthkit order_by SOURCE_FILE TARGET_FILE KEY [KEY ...]

At least one key is required. Each key can be specified in one of these forms:

* ``KEY`` uses ascending order.
* ``KEY=ascending`` explicitly requests ascending order.
* ``KEY=descending`` requests descending order.
* ``KEY=value1,value2,...`` specifies a custom value order.

Direction names must be ``ascending`` or ``descending``. Each key may appear
only once. Pass multiple keys as separate arguments, not as a comma-separated
list of key names.

Ordering priority
-----------------

Keys are applied in the order given. The first key has the highest priority;
later keys order messages that have equal values for earlier keys.

.. code-block:: bash

   earthkit order_by input.grib ordered.grib parameter.variable vertical.level
   earthkit order_by input.grib ordered.grib vertical.level parameter.variable

The first example groups fields by variable, then sorts levels within each
variable. The second sorts by level first, then by variable within each level.
Directions can be mixed:

.. code-block:: bash

   earthkit order_by input.grib ordered.grib parameter.variable=ascending vertical.level=descending

Custom value orders
-------------------

A comma-separated list defines the desired sequence of values for a key.
It must include all values present in the input for that key. Values must be
non-empty and unique. Unlike ``sel``, colons are not expanded into ranges.

.. code-block:: bash

   earthkit order_by input.grib ordered.grib parameter.variable=u,t,v
   earthkit order_by input.grib ordered.grib vertical.level=700,300,1000,400,850,500 parameter.variable=v,u,t

These examples assume the input contains only the listed variables and levels.
Numeric metadata values are handled by the underlying ordering API. Quote
arguments if custom values contain spaces.

GRIB and BUFR
-------------

GRIB input is converted to a FieldList and ordered with
:meth:`earthkit.data.core.fieldlist.FieldList.order_by`. Use the metadata keys
accepted by that method, for example ``parameter.variable``, ``vertical.level``
or ``metadata.paramId``.

BUFR input is converted to a FeatureList and ordered by message header metadata.
For example:

.. code-block:: bash

   earthkit order_by input.bufr ordered.bufr ident
   earthkit order_by input.bufr ordered.bufr dataCategory ident=descending

Custom orders preserve string identifiers with leading zeroes, but must list
every identifier present in the input.

Ordering does not select or discard messages. To select a subset before ordering,
write it with :doc:`sel`, then use that file as the ordering input:

.. code-block:: bash

   earthkit sel input.grib selected.grib parameter.variable=t,u
   earthkit order_by selected.grib ordered.grib parameter.variable vertical.level=descending

The CLI does not expose Python-only arguments such as remapping dictionaries,
patch dictionaries or custom comparator callables.
