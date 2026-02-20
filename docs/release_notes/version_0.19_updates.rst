
Version 0.19 Updates
/////////////////////////



Version 0.19.1
===============

Fixes
++++++++

- Fixed a bug in the CDS source when could load not cached data when no network connection was available (:pr:`906`).


Version 0.19.0
===============

Deprecations
+++++++++++++++++++

- :ref:`deprecated-array-backend-kwarg`
- :ref:`deprecated-field-array-backend-attribute`


Refactored array backends
++++++++++++++++++++++++++++++

.. note::

    The array backend implementation in :xref:`earthkit-utils` has been refactored. The minimum required version of :xref:`earthkit-utils` is now ``0.2.0`` (:pr:`842`).


The API for the array backends has been slightly modified to accommodate new features and improvements in :xref:`earthkit-utils`:

- the ``array_backend`` kwarg is now deprecated and ``array_namespace`` should be used instead. This affects the following methods: :func:`Field.to_array`, :func:`Field.copy`,  :func:`Field.clone`, :func:`FieldList.to_array`, :func:`FieldList.to_fieldlist`, :func:`to_xarray`.
- the ``Field.array_backend`` attribute is now deprecated and ``Field.array_namespace`` should be used instead
- as an experimental feature the ``device`` kwarg is now supported in most of the above methods to specify the device where the array should be created (e.g. ``"cpu"``, ``"cuda:0"``)


New features
++++++++++++++++++++++++++++++

- Added support for reading UK Met Office PP binary files (:pr:`838`). See the notebook example:

    - :ref:`/examples/ukmo_pp.ipynb`
- Added the ``copy()`` method to CodesHandle (:pr:`882`).

Changes
++++++++++++++++++++++++++++++

- Xarray/NetCDF data on an unstructured grid is now parsed into a fieldlist. For example, NetCDF data with the following structure::

        Dimensions: ... point=200
        Coordinates:
        * point    (point) int64 0 1 2 3 4 ... 196 197 198 199
        * latitudes  (point) float32 34.5 34.6 ... 36.7 36.8
        * longitudes  (point) float32 -120.0 -119.9 ...
        Data variables:
        * temperature  (point) float32 ...
        * humidity  (point) float32 ...

  is now parsed into a fieldlist with two fields:

  .. code-block:: Python

      >>> import earthkit.data as ekd
      >>> ds = ekd.from_source("file", "data.nc")
      >>> len(ds)
      2

  Previously, this data would have been parsed into an XarrayDatasetWrapper.

- Added support to convert GRIB "stepRange" values to timedelta (:pr:`837`).
- Use the "order" key instead of "ordering" in gridspecs generated for HEALPix grids (:pr:`853`).
- :py:func:`earthkit.data.utils.humanize.did_you_mean` now raises a ``ValueError`` if no vocabulary is provided (:pr:`855`).

Fixes
++++++++

- Fixed cloning of Xarray fields (:pr:`841`).



Installation
++++++++++++++++++++++++++++++

- The minimum required version of Python is now 3.10
