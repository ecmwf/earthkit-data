Version 0.11 Updates
/////////////////////////


Version 0.11.0
===============

New Xarray engine
++++++++++++++++++

- Added new Xarray engine called ``"earthkit"``. This is the new default when calling :meth:`~data.core.fieldlist.FieldList.to_xarray`. The ``"cfgrib"`` engine is still available and can be used by passing ``engine="cfgrib"`` to :meth:`~data.core.fieldlist.FieldList.to_xarray`. For details see:

  - :ref:`xr_engine`
  - :ref:`examples_xr_engine` (notebook examples)

API changes
+++++++++++++

- No array backend is assigned to a Fieldlist any longer. Removed the ``array_backend`` property from FieldList, and the ``array_backend`` keyword from :func:`from_source`. Data accessing methods like :py:meth:`to_array` and :py:meth:`data` still accept the ``array_backend`` option. Now, each Field in a FieldList can have a different array backend reflecting the actual storage type of the values (:pr:`471`).

  You can still create a :py:class:`SimpleFieldList` with a single array backend by using the :meth:`~data.core.fieldlist.FieldList.to_fieldlist` method. For example:

  .. code-block:: python

      # Old way
      fields = from_source("file", "my.grib", array_backend="pytorch").to_fieldlist()

      # New way
      ds = from_source("file", "my.grib").to_fieldlist(array_backend="pytorch")

- Removed :py:class:`ArrayFieldList`. Its functionality is covered by :py:class:`SimpleFieldList` (:pr:`471`).
- :meth:`~data.core.fieldlist.FieldList.from_array` and :meth:`~data.core.fieldlist.FieldList.to_fieldlist` now return an :py:class:`SimpleFieldList`

See :ref:`/examples/grib_array_backends.ipynb` for more details.


Changes
++++++++
- Added the :ref:`data-sources-s3` source to access AWS S3 buckets (:pr:`484`). See the notebook examples:

  - :ref:`/examples/s3.ipynb`

- Added support for geotiff files (:pr:`503`). See the notebook examples:

  - :ref:`/examples/geotiff.ipynb`

- Added :ref:`stream <streams>` support for the :ref:`data-sources-file` source (:pr:`500`)
- Allowed concatenation of :ref:`stream <streams>` sources (:pr:`500`)
- Added :py:class:`SimpleFieldList`, which can store a list of arbitrary Fields (:pr:`471`). See the notebook examples:

  - :ref:`/examples/grib_array_backends.ipynb`

- Added :meth:`~data.core.fieldlist.Field.clone` and :py:meth:`~data.core.fieldlist.Field.copy` to alter field metadata and values (:pr:`493`, :pr:`496`, :pr:`522`). See the notebook examples:

  - :ref:`/examples/grib_modification.ipynb`

- Reimplemented and documented the :ref:`data-sources-lod` source, which is now generating a :py:class:`SimpleFieldList` and is not bound to GRIB specific metadata (:pr:`461`, :pr:`511`). See the notebook examples:

  - :ref:`examples_lod`

- Added serialisation to GRIB fieldlists and Metadata (:pr:`463`, :pr:`474`)
- Improved in-memory GRIB field implementation (:pr:`492`)
- Enabled to use :ref:`data-sources-forcings` without providing a source (:pr:`495`)
- Implemented the repr to ArrayField by (:pr:`455`)
- Added ``remapping`` option to :py:meth:`Field.metadata` (:pr:`488`)
- Added ``handle`` property to ArrayField (:pr:`464`)
- Added the :py:func:`Field.to_xarray`, :py:func:`Field.ls` and :py:func:`Field.describe` methods (:pr:`513`)
- Allowed logging control for :ref:`data-sources-mars` source (:pr:`457`)
- Added support for "lambert_azimuthal_equal_area" metadata (:pr:`452`)


Fixes
+++++

- Use FileNotFoundError when no file found rather than FileExistsError (:pr:`479`)
