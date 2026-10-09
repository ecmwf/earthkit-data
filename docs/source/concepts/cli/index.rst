Command line interface
======================

Installing earthkit-data makes its commands available through the shared
``earthkit`` command line interface. Use ``earthkit COMMAND --help`` to display
the syntax and options for a command.

The following commands select or reorder data and write the result to a target:

.. toctree::
   :maxdepth: 1

   sel
   order_by

Sources and targets
-------------------

Both commands take a ``SOURCE`` and a ``TARGET``, given in the same way as for the
other ``earthkit`` commands, as ``[NAME:]VALUE``:

* A file path, e.g. ``input.grib``, is the same as ``file:input.grib``. Glob
  patterns such as ``'data/*.grib'`` are allowed for the source.
* Any other earthkit-data source can be used, e.g. ``url:https://myhost.int/file.grib``
  or a JSON request such as ``'mars:{"param": "2t", "levtype": "sfc"}'``.
* Several sources are merged, e.g. ``earthkit sel a.grib b.grib selected.grib ...``.
* ``-`` reads GRIB data from stdin, or writes to stdout, so commands can be piped:

.. code-block:: bash

   cat input.grib | earthkit order_by - - -k vertical.level | earthkit sel - selected.grib --parameter.variable t

A target file must differ from the source files, including through symbolic or
hard links. An existing target file may be overwritten. The target suffix
determines the output format through the available file encoders; use the same
format as the source when selecting or reordering without format conversion.
