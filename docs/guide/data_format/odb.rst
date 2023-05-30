.. _odb:


ODB
---------

:xref:`odb` is a bespoke format developed at ECMWF to store observations.

to_pandas()
++++++++++++++

The recommended way to work with ODB is to extract data with ``to_pandas()`` into a pandas DataFrame. The ODB data extraction in ``to_pandas()`` is implemented by :xref:`pyodc`.

Examples:

    - :ref:`/examples/odb.ipynb`
