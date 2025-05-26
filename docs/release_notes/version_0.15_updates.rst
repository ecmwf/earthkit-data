Version 0.15 Updates
/////////////////////////


Version 0.15.0
===============

Xarray engine
++++++++++++++++++++++++++++++

- Improved the serialisation of GRIB fieldlists to reduce memory usage when Xarray is generated with chunks (:pr:`700`). See the :ref:`/examples/xarray_engine_chunks.ipynb` notebook example.
- TensorBackendArray, which implements the lazy loading of DataArrays in the Xarray engine, now uses a ``dask.utils.SerializableLock`` when accessing the data (:pr:`700`).
- Enabled converting :ref:`data-sources-lod` fieldlists into Xarray (:pr:`701`). See the :ref:`/examples/list_of_dicts_to_xarray.ipynb` notebook example.


New features
+++++++++++++++++

- Added new config option ``grib-file-serialisation-policy`` to control how GRIB data on disk is pickled. The options are "path" and "memory". The default is "path". Previously, only "memory" was implemented (:pr:`700`).
- Added serialisation to GRIB fields (both on disk and in-memory) (:pr:`700`)


Fixes
+++++++++++++++++

- Fixed issue when the :ref:`data-sources-forcings` source  did not handle time-zone aware datetimes correctly (:pr:`693`).
