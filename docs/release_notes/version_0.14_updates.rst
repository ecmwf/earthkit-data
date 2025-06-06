Version 0.14 Updates
/////////////////////////


Version 0.14.4
===============

Fixes
++++++

- Fixed issue when getting the "gridSpec" GRIB metadata key with a default value caused a crash when ecCodes 2.41.0 was used. (:pr:`719`).
- Now, dependencies for GeoTIFF support are not installed when earthkit-data is installed with ``pip install earthkit-data[all]``. This step was necessary to make installation work when GDAL is not available. These dependencies need to be installed separately with ``pip install earthkit-data[geotiff]``. See :ref:`install`. (:pr:`718`).


Version 0.14.3
===============

Fixes
+++++++++++++++++

- Fixed issue when getting GRIB metadata for the "geography" namespace caused a crash when the "bitmap" key was present in the namespace. The "bitmap" key is now ignored in the "geography" namespace.

Version 0.14.2
===============

Fixes
+++++++++++++++++

- Fixed issue when the :ref:`data-sources-file-pattern` source did not return the right data object when the ``hive_partitioning`` option was set to ``False`` (:pr:`697`).
- Fixed issue when disabling the ``add_earthkit_attrs`` option in :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` caused a crash (:pr:`696`).


Version 0.14.1
===============

Fixes
+++++++++++++++++

- Fixed issue when Xarray computations used excessive memory when the data was created with the Xarray engine using chunking (:pr:`694`).

Version 0.14.0
===============

CDS/ADS retrievals
+++++++++++++++++++++

The date request parameter(s) in the :ref:`data-sources-cds` and :ref:`data-sources-ads` sources are now passed without any normalization to the underlying API. Previously, date parameters were normalised using the same set of rules as defined for :ref:`data-sources-mars` requests leading to inconsistencies. This is a **breaking change** enforcing the use of the CDS date syntax in :ref:`data-sources-cds` and :ref:`data-sources-ads` retrievals (:pr:`605`)


Xarray engine ``split_dims``
++++++++++++++++++++++++++++++

When :meth:`~data.core.fieldlist.FieldList.to_xarray` is called with ``split_dims``, the engine will now return a tuple with two lists: the first list contains the Xarray datasets, while the second one contains the corresponding dictionaries with the spitting keys/values (one dictionary per dataset) (:pr:`688`). Previously, a list of datasets was returned so this is a **breaking change**.

See the :ref:`/examples/xarray_engine_split.ipynb` notebook example.


Patterns
+++++++++++++++++++++++++++++

The ``allow_missing_keys`` keyword argument was removed from :py:meth:`Patterns.__init__`. When :py:class:`Patterns` was created with ``allow_missing_keys=True`` it allowed passing parameters to :py:meth:`Patterns.substitue` which were not part of the pattern. This behaviour can now be controlled by passing the ``allow_extra=True`` keyword argument to each :py:meth:`Patterns.substitue` call. This is a **breaking change** (:pr:`659`).

New features
+++++++++++++++++

- Added the ``hive_partitioning`` option to the :ref:`data-sources-file-pattern` source to allow running :func:`sel` effectively on GRIB data stored in a :ref:`hive partitioning <file-pattern-hive-partioning>` structure (:pr:`659`).
- Added experimental support for lazy loading FDB data (:pr:`677`). See the ``lazy`` option in the :ref:`data-sources-fdb` source for details.
- Added the ``flatten`` argument to the :func:`to_numpy` methods of the Xarray DataArray and Dataset wrapper classes (:pr:`685`).
- Implemented the :func:`override` and :func:`dump` methods for :py:class:`UserMetadata` (:pr:`683`)
- Added support for the ``bigtiff`` format (:pr:`656`).
- The array backend related code was moved to the ``earthkit-utils`` package, which became a new dependency(:pr:`672`).

Fixes
+++++++++++++++++

- Fixed issue when using ``split_dims`` with multiple keys in the Xarray engine did not work correctly (:pr:`688`).
- Fixed issue when :py:class:`UserMetadata` crashed when could not access the data values. With this fix nor the data values neither their shape is required for :py:class:`UserMetadata` (:pr:`681`).
