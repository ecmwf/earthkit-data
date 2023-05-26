Installation
============

Installing earthkit-data
----------------------------

Install **earthkit-data** with python3 (>= 3.8) and ``pip`` as follows:

.. code-block:: bash

    python3 -m pip install earthkit-data

Alternatively, install via ``conda`` with:

.. code-block:: bash

    conda install earthkit-data -c conda-forge

This will bring in some necessary binary dependencies for you.

Installing the binary dependencies
--------------------------------------

ecCodes
+++++++++++

**earthkit-data** depends on the ECMWF :xref:`eccodes` library
that must be installed on the system and accessible as a shared library.

When earthkit-data is installed from ``conda`` ecCodes will **also be installed** for you. Otherwise, you need to install it using one of the following methods:

    - The easiest way to install it is to use ``conda``:

        .. code-block:: bash

            conda install eccodes -c conda-forge

    - On a MacOS it is also available from ``HomeBrew``:

        .. code-block:: bash

            brew install eccodes

    - As an alternative you may install the official source distribution by following the instructions `here <https://software.ecmwf.int/wiki/display/ECC/ecCodes+installation>`_.

FDB
+++++

For FDB (Fields DataBase) access FDB5 must be installed on the system. See the `FDB documentation <https://fields-database.readthedocs.io/en/latest/>`_ for details.
