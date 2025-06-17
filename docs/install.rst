.. _install:

Installation
============

Installing from PyPI
------------------------------------

Minimal installation
+++++++++++++++++++++++++

Install **earthkit-data** with python3 (>= 3.9) and ``pip`` as follows:

.. code-block:: bash

    python3 -m pip install earthkit-data

The package installed like this is **minimal** supporting only GRIB and NetCDF data and cannot access remote services other than URLs. If you want to use more data types or remote services you need to install the optional Python packages.

Installing all the optional packages
++++++++++++++++++++++++++++++++++++++++

You can install **earthkit-data** with all the optional packages (with the exception of the "geotiff" and "zarr" dependencies, see below) in one go by using:

.. code-block:: bash

    python3 -m pip install earthkit-data[all]

Please note in **zsh** you need to use quotes around the square brackets:

.. code-block:: bash

    python3 -m pip install "earthkit-data[all]"


Installing individual optional packages
+++++++++++++++++++++++++++++++++++++++++

Alternatively, you can install the following components:

    - mars: provides access to the :ref:`data-sources-mars` source
    - cds: provides access to the :ref:`data-sources-cds` and :ref:`data-sources-ads` sources
    - ecmwf-opendata: provides access to the :ref:`data-sources-eod`
    - wekeo: provides access to the :ref:`data-sources-wekeo` and :ref:`data-sources-wekeocds` sources
    - fdb: provides access to the :ref:`data-sources-fdb` source
    - polytope: provides access to the :ref:`data-sources-polytope` source
    - odb: provides full support for the :ref:`odb` data type
    - geo: enables to use the :py:meth:`Field.points_unrotated()` method
    - geopandas: adds GeoJSON/GeoPandas support
    - projection: adds projection support
    - covjsonkit: provides access to CoverageJSON data served by the :ref:`data-sources-polytope` source
    - s3: provides access to non-public :ref:`s3 <data-sources-s3>` buckets (new in version *0.11.0*)
    - geotiff: adds GeoTIFF support (new in version *0.11.0*). Please note that this is not included in the ``[all]`` option and has to be invoked separately.
    - zarr: provides access to the :ref:`data-sources-zarr` source (new in version *0.15.0*). Please note that this is not included in the ``[all]`` option and has to be invoked separately.

E.g. to add :ref:`data-sources-mars`  support you can use:

.. code-block:: bash

    python3 -m pip install earthkit-data[mars]

List of optional dependencies can also be specified :

.. code-block:: bash

    python3 -m pip install earthkit-data[cds,mars]


Installing with conda
---------------------------------------

Install **earthkit-data** via ``conda`` with:

.. code-block:: bash

    conda install earthkit-data -c conda-forge

This will bring in some necessary binary dependencies for you.


Installing the binary dependencies
--------------------------------------

FDB
+++++

For FDB (Fields DataBase) access FDB5 must be installed on the system. See the `FDB documentation <https://fields-database.readthedocs.io/en/latest/>`_ for details.
