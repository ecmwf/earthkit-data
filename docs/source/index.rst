Earthkit-data's documentation
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


**earthkit-data** is a format-agnostic Python interface for geospatial data with a focus on meteorology and
climate science. It is the data handling component of :xref:`earthkit`.

**earthkit-data** makes it simple to read, inspect and slice data from a wide range of
geospatial input types (:ref:`grib`, :ref:`netcdf` and more) and transform them into
familiar scientific Python objects (including numpy arrays, pandas dataframes, xarray datasets).

**earthkit-data** provides additional convenient methods for quickly inspecting certain
features of your input data, such as data dimensionality, axes, coordinate
reference systems and bounding boxes.


.. grid::  1 1 2 2
   :gutter: 2

   .. grid-item-card:: Installation and Getting Started
      :img-top: _static/rocket.svg
      :link: getting-started
      :link-type: doc
      :class-card: sd-shadow-sm

      New to earthkit-data? Start here with installation and a quick overview.

   .. grid-item-card:: Frequently Asked Questions
      :img-top: _static/message-question.svg
      :link: getting-started
      :link-type: doc
      :class-card: sd-shadow-sm

      The most common questions, answered.

   .. grid-item-card:: Tutorials
      :img-top: _static/book.svg
      :link: tutorials/index
      :link-type: doc
      :class-card: sd-shadow-sm

      Step-by-step guides to learn earthkit-data.

   .. grid-item-card:: How-tos
      :img-top: _static/tool.svg
      :link: how-tos/index
      :link-type: doc
      :class-card: sd-shadow-sm

      Practical recipes for common tasks.

   .. grid-item-card:: Concepts
      :img-top: _static/bulb.svg
      :link: concepts/index
      :link-type: doc
      :class-card: sd-shadow-sm

      Understand the core ideas behind earthkit-data.

   .. grid-item-card:: API Reference Guide
      :img-top: _static/brackets-contain.svg
      :link: api-reference
      :link-type: doc
      :class-card: sd-shadow-sm

      Detailed documentation of all functions and classes.

**Support**

Have a feature request or found a bug? Feel free to open an
`issue <https://github.com/ecmwf/earthkit-data/issues/new/choose>`_.


.. toctree::
   :caption: User guide
   :maxdepth: 2
   :hidden:

   getting-started
   faq
   tutorials/index
   how-tos/index
   concepts/index
   api-reference
   faqs

.. toctree::
   :caption: Developer guide
   :maxdepth: 2
   :hidden:

   development/index


.. toctree::
   :maxdepth: 2
   :caption: Extras
   :hidden:

   release-notes/index
   licence
   genindex
