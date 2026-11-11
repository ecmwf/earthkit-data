Selecting data by position with isel
====================================

``earthkit isel`` selects GRIB fields, BUFR messages or NetCDF data by position
and writes the result to a target. It is the positional counterpart of
:doc:`sel`, which selects by value.

Syntax
------

.. code-block:: bash

   earthkit isel SOURCE TARGET --KEY INDEX [--KEY INDEX ...]

See :doc:`index` for the forms of ``SOURCE`` and ``TARGET``. At least one
condition is required, and each key can be given once. ``--KEY=INDEX`` can be
used instead of ``--KEY INDEX``. Negative indexes need no quoting, e.g.
``--vertical.level -1``.

``INDEX`` uses the same syntax as the ``-i/--index`` option of other ``earthkit``
commands:

* an integer, e.g. ``0``, or a negative one counting from the end, e.g. ``-1``
* a comma-separated list, e.g. ``0,2,5``
* a slice ``START:STOP[:STEP]``, e.g. ``1:3``, ``2:`` or ``::2``

Indexes start at 0. Unlike ``sel``, slices **exclude** ``STOP``, as in Python.

What a position refers to
-------------------------

* **GRIB and BUFR**: ``KEY`` is an earthkit-data metadata key, and ``INDEX`` is
  the position in the **sorted unique values** of that key. This is the order the
  dimension would have when the data is converted to Xarray.
* **NetCDF**: ``KEY`` is a dimension name, and ``INDEX`` is the position along
  that dimension, in the order of the file. An integer ``INDEX`` drops the
  dimension, as ``xarray.Dataset.isel`` does.

Conditions on different keys are combined with AND.

Examples
--------

With ``tuv_pl.grib``, which has the levels 300, 400, 500, 700, 850 and 1000:

.. code-block:: bash

   earthkit isel tuv_pl.grib out.grib --vertical.level 0          # 300
   earthkit isel tuv_pl.grib out.grib --vertical.level -1         # 1000
   earthkit isel tuv_pl.grib out.grib --vertical.level 1:3        # 400 and 500
   earthkit isel tuv_pl.grib out.grib --vertical.level ::2        # 300, 500 and 850
   earthkit isel tuv_pl.grib out.grib --vertical.level 0,5 --parameter.variable 0

   earthkit isel tuv_pl.nc out.nc --level 0:2 --latitude -1

   cat tuv_pl.grib | earthkit isel - - --vertical.level -1 > top.grib

Errors
------

An index outside the available values, an index that selects nothing (e.g.
``4:2``), a GRIB or BUFR key without values, or a NetCDF name that is not a
dimension is reported as a usage error naming the option.
