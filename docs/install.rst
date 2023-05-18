Installation
============

Installing earthkit-data
----------------------------

**earthkit-data** can be installed from PyPI with:

.. code-block:: bash

    pip install earthkit-data


Installing the binary dependencies
--------------------------------------

**earthkit-data** depends on the ECMWF *ecCodes* library
that must be installed on the system and accessible as a shared library. The easiest way to install it is to use Conda:

.. code-block:: bash

    conda install eccodes -c conda-forge


On a MacOS it is also available from HomeBrew:

.. code-block:: bash

    brew install eccodes

As an alternative you may install the official source distribution
by following the instructions at
https://software.ecmwf.int/wiki/display/ECC/ecCodes+installation
