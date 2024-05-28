Version 0.8 Updates
/////////////////////////

Version 0.8.0
===============

Streams
++++++++++++

Refactored the stream source interface:

- added :py:meth:`~data.core.fieldlist.FieldList.batched` and :meth:`~data.core.fieldlist.FieldList.group_by` for stream and fieldlist like objects
- added the ``read_all`` option for :func:`from_source` to read all data into memory when ``stream=True``
- removed the ``batch_size`` and ``group_by`` kwargs from :func:`from_source`

See :ref:`here <streams>` for further details.


New features
++++++++++++++++

- Removed warning when non default (non-forced) options in ``xarray_open_dataset_kwargs`` passed to :meth:`~data.readers.grib.index.GribFieldList.to_xarray` for GRIB data.
- Used warnings.warn() when forced kwargs (``errors`` or ``engine``) specified with non-default values to :meth:`~data.readers.grib.index.GribFieldList.to_xarray` for GRIB data.
- Enabled earthkit-data to be used in anemoi-datasets


Fixes
++++++

- Fixed issue when :func:`from_source` could not be used after importing GRIBReader.
