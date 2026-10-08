Command line interface
======================

Installing earthkit-data makes its commands available through the shared
``earthkit`` command line interface. Use ``earthkit COMMAND --help`` to display
the syntax and options for a command.

The following commands select or reorder data and write the result to a file:

.. toctree::
   :maxdepth: 1

   sel
   order_by

Both commands require an existing source file and a different target file.
They also reject symbolic or hard links that refer to the source file.
An existing target file may be overwritten. The target suffix determines the
output format through the available file encoders; use the same format as the
source when selecting or reordering without format conversion.
