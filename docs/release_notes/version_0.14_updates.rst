Version 0.14 Updates
/////////////////////////


Version 0.14.0
===============

CDS/ADS retrievals
+++++++++++++++++++++

The date request parameter(s) in the :ref:`data-sources-cds` and :ref:`data-sources-ads` sources are now passed without any normalization to the underlying API. Previously, date parameters were normalised using the same set of rules as defined for :ref:`data-sources-mars` requests leading to inconsistencies. This is a **breaking change** enforcing the use of the CDS date syntax in :ref:`data-sources-cds` and :ref:`data-sources-ads` retrievals (:pr:`605`)


Xarray engine ``split_dims``
++++++++++++++++++++++++++++++

When :meth:`~data.core.fieldlist.FieldList.to_xarray` is called with ``split_dims``, the engine will now return a tuple with two lists: the first list contains the Xarray datasets, while the second one contains the corresponding dictionaries with the spitting keys/values (one dictionary per dataset) (:pr:`688`). Previously, a list of datasets was returned so this is a **breaking change**.

See the :ref:`/examples/xarray_engine_split.ipynb` notebook example.


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
