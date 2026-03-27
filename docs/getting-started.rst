
Installation and Getting Started
================================

Installing from PyPi
--------------------

Install **earthkit-data** with python3 (>= 3.10) and ``pip`` as follows:

.. code-block:: bash

    python3 -m pip install earthkit-data

The package installed like this is **minimal** supporting only GRIB and NetCDF data and cannot access remote services other than URLs. If you want to use more data types or remote services you need to install the optional Python packages.

For more details on the installation please see :ref:`install`.


Import and use
--------------

.. code-block:: python

    import earthkit.data as ekd

    data = ekd.from_source("sample", "test.grib")
    fl = data.to_fieldlist()
    arr = data.to_numpy()
    df = data.to_pandas()
    dataset = data.to_xarray()
