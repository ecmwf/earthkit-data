.. _install:

Installation
============

Installing from PyPI
------------------------------------

Minimal installation
+++++++++++++++++++++++++

Install **earthkit-data** with python3 (>= 3.10 ) and ``pip`` as follows:

.. code-block:: bash

    python3 -m pip install earthkit-data>=1.0.0rc0

The package installed like this is **minimal** supporting only GRIB and NetCDF data and cannot access remote services other than URLs. If you want to use more data types or remote services you need to install the optional Python packages.

Installing all the optional packages
++++++++++++++++++++++++++++++++++++++++

You can install **earthkit-data** with all the optional packages (with the exception of the "geotiff" and "zarr" dependencies, see below) in one go by using:

.. code-block:: bash

    python3 -m pip install earthkit-data[all]>=1.0.0rc0

Please note in **zsh** you need to use quotes around the square brackets:

.. code-block:: bash

    python3 -m pip install "earthkit-data[all]>=1.0.0rc0"


Installing individual optional packages
+++++++++++++++++++++++++++++++++++++++++

Alternatively, you can install the following components:

    - cds: provides access to the :ref:`data-sources-cds` and :ref:`data-sources-ads` sources
    - covjsonkit: provides access to CoverageJSON data served by the :ref:`data-sources-polytope` source
    - ecmwf-opendata: provides access to the :ref:`data-sources-eod`
    - fdb: provides access to the :ref:`data-sources-fdb` source
    - geotiff: adds GeoTIFF support (new in version *0.11.0*). Please note that this is not included in the ``[all]`` option and has to be invoked separately.
    - geopandas: adds GeoJSON/GeoPandas support
    - gribjump: provides access to the :ref:`data-sources-gribjump` source
    - iris: provides access to UK Met Office PP files (new in version *0.19.0*).
    - mars: provides access to the :ref:`data-sources-mars` source
    - odb: provides full support for the :ref:`odb` data type
    - projection: adds projection support
    - polytope: provides access to the :ref:`data-sources-polytope` source
    - s3: provides access to non-public :ref:`s3 <data-sources-s3>` buckets (new in version *0.11.0*)
    - wekeo: provides access to the :ref:`data-sources-wekeo` and :ref:`data-sources-wekeocds` sources
    - zarr: provides access to the :ref:`data-sources-zarr` source (new in version *0.15.0*). Please note that this is not included in the ``[all]`` option and has to be invoked separately.

E.g. to add :ref:`data-sources-mars`  support you can use:

.. code-block:: bash

    python3 -m pip install earthkit-data[mars]>=1.0.0rc0

List of optional dependencies can also be specified :

.. code-block:: bash

    python3 -m pip install earthkit-data[cds,mars]>=1.0.0rc0



Installing the binary dependencies
--------------------------------------

FDB
+++++

For FDB (Fields DataBase) access FDB5 must be installed on the system. See the `FDB documentation <https://fields-database.readthedocs.io/en/latest/>`_ for details.


GribJump
++++++++++++

For FDB access with GribJump, both FDB5 and GribJump must be installed on the system. See the `GribJump project <https://github.com/ecmwf/gribjump>`_ for details.
