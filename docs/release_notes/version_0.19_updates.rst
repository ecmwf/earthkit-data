
Version 0.19.0 Updates
===================================


Deprecations
+++++++++++++++++++

- :ref:`deprecated-array-backend-kwarg`
- :ref:`deprecated-field-array-backend-attribute`


Refactored array backends
++++++++++++++++++++++++++++++

.. note::

    The array backend implementation in :xref:`earthkit-utils` has been refactored. With this ``earthkit-data`` now requires at least :xref:`earthkit-utils` version ``0.2.0`` (:pr:`842`).

The API for the array backends has been slightly modified to accommodate new features and improvements in :xref:`earthkit-utils`:

- the ``array_backend`` kwarg is now deprecated and ``array_namespace`` should be used instead. This affects the following methods: :func:`Field.to_array`, :func:`Field.copy`,  :func:`Field.clone`, :func:`FieldList.to_array`, :func:`FieldList.to_fieldlist`, :func:`to_xarray`.
- the ``Field.array_backend`` attribute is now deprecated and ``Field.array_namespace`` should be used instead
- as an experimental feature the ``device`` kwarg is now supported in most of the above methods to specify the device where the array should be created (e.g. ``"cpu"``, ``"cuda:0"``)


New features
++++++++++++++++++++++++++++++

- Added support for reading UK Met Office PP binary files (:pr:`838`). See the notebook example:

    - :ref:`/examples/iris_pp.ipynb`


Changes
++++++++++++++++++++++++++++++

- Added support to convert GRIB "stepRange" values to timedelta (:pr:`837`)
- Use the "order" key instead of "ordering" in gridspecs generated for HEALPix grids (:pr:`853`).

Fixes
++++++++

- Fixed cloning of Xarray fields (:pr:`841`).
