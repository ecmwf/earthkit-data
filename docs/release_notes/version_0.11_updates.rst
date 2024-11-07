Version 0.11 Updates
/////////////////////////


Version 0.11.0
===============

New features
++++++++++++++

- added new Xarray engine called ``"earthkit"``. This is the new default when calling :meth:`~data.core.fieldlist.FieldList.to_xarray`. The ``"cfgrib"`` engine is still available and can be used by passing ``engine="cfgrib"`` to :meth:`~data.core.fieldlist.FieldList.to_xarray`. For details see:

  - :ref:`xr_engine`
  - :ref:`examples_xr_engine` (notebook examples)

- added new :ref:`data-sources-s3` source to access AWS S3 buckets. See the :ref:`/examples/s3.ipynb` notebook example. (:pr:`484`)
- add :ref:`stream <streams>` support for :ref:`data-sources-file` source (:pr:`500`)
- allowed concatenation of :ref:`stream <streams>` sources (:pr:`500`)
- TODO: refactor array fieldlists (:pr:`471`
- TODO: alter field metadata (:pr:`493`)
- TODO: alter field values (:pr:`496`)
- TODO: :ref:`data-sources-lod` source. See notebooks: :ref:`examples_lod` (:pr:`461`, :pr:`511`)
- added serialisation to GRIB fieldlists and Metadata (:pr:`463`, :pr:`474`)
- TODO: improved in-memory GRIB field implementation (:pr:`492`)
- enabled to use :ref:`data-sources-forcings` without providing a source (:pr:`495`)
- implemented the repr to ArrayField by (:pr:`455`)
- added ``remapping`` option to :py:meth:`Field.metadata` (:pr:`488`)
- added ``handle`` property to ArrayField (:pr:`464`)
- added the :py:func:`Field.to_xarray`, :py:func:`Field.ls` and :py:func:`Field.describe` methods (:pr:`513`)
- allowed logging control for :ref:`data-sources-mars` source (:pr:`457`)
- added support for "lambert_azimuthal_equal_area" metadata (:pr:`452`)

Other
++++++
-  Use the ``covjsonkit`` package instead of ``eccovjson`` (:pr:`445`)

Fixes
+++++

- Use FileNotFoundError when no file found rather than FileExistsError (:pr:`479`)
