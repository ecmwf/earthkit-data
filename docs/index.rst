Welcome to earthkit-data's documentation
======================================================

|Static Badge| |image1| |License: Apache 2.0| |Latest
Release|

.. |Static Badge| image:: https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE/foundation_badge.svg
   :target: https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE
.. |image1| image:: https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity/incubating_badge.svg
   :target: https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity
.. |License: Apache 2.0| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: https://opensource.org/licenses/apache-2-0
.. |Latest Release| image:: https://img.shields.io/github/v/release/ecmwf/earthkit-data?color=blue&label=Release&style=flat-square
   :target: https://github.com/ecmwf/earthkit-data/releases


.. important::

    This software is **Incubating** and subject to ECMWF's guidelines on `Software Maturity <https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity>`_.


**earthkit-data** is a format-agnostic Python interface for geospatial data with a focus on meteorology and
climate science. It is the data handling component of :xref:`earthkit`.

**earthkit-data** makes it simple to read, inspect and slice data from a wide range of
geospatial input types (:ref:`grib`, :ref:`netcdf` and more) and transform them into
familiar scientific Python objects (including numpy arrays, pandas dataframes, xarray datasets).

**earthkit-data** provides additional convenient methods for quickly inspecting certain
features of your input data, such as data dimensionality, axes, coordinate
reference systems and bounding boxes.

Quick start
-----------

.. code-block:: python

    import earthkit.data as ekd

    data = ekd.from_source("sample", "test.grib")
    arr = data.to_numpy()
    df = data.to_pandas()
    dataset = data.to_xarray()


.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/index

.. toctree::
   :maxdepth: 1
   :caption: Documentation

   howtos
   guide/index
   api
   development

.. toctree::
   :maxdepth: 1
   :caption: Installation

   install
   release_notes/index
   licence

.. toctree::
   :maxdepth: 1
   :caption: Plugins

   plugins/index

.. toctree::
   :maxdepth: 1
   :caption: Projects

   earthkit <https://earthkit.readthedocs.io/en/latest>


Indices and tables
==================

* :ref:`genindex`

.. * :ref:`modindex`
.. * :ref:`search`
