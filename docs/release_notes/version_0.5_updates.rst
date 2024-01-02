Version 0.5 Updates
/////////////////////////

Version 0.5.0
===============

New features
++++++++++++++++

- changed the default :ref:`cache policy <cache_policies>` to :ref:`off <off_cache_policy>`, which now enables the usage of remote sources like :ref:`data-sources-mars`. See the :ref:`/examples/cache.ipynb` notebook example.
- allowed defining source :ref:`plugins <plugin-overview>`
- enabled reading :ref:`data-sources-url` sources as streams. See the :ref:`/examples/grib_url_stream.ipynb` notebook example
- added the :meth:`FieldList.to_fieldlist() <data.core.fieldlist.FieldList.to_fieldlist>`  method to convert to a new :class:`FieldList` based on a given backend
- added the :meth:`nearest_point_haversine` and :meth:`nearest_point_kdtree` methods to find the nearest point out of a set of locations. See the :ref:`/examples/grib_nearest_gridpoint.ipynb` and :ref:`/examples/grib_time_series.ipynb` notebook examples.
- enabled using dictionaries in the ``split_on`` request parameter for :ref:`data-sources-cds` retrievals
- added the experimental "constants" source type
- ensured consistent usage of ``pandas_read_csv_kwargs`` for :ref:`data-sources-file` and :ref:`data-sources-cds` sources


Fixes
++++++
- fixed issue when slicing did not work on :class:`~data.core.fieldlist.FieldList` filtered with ``sel()``
- fixed crash in :meth:`FieldList.to_xarray() <data.core.fieldlist.FieldList.to_xarray>` when  the ``filter_by_keys`` option in ``backend_kwargs`` was used
- fixed issue when list of dates could not be used in a :ref:`data-sources-cds` request
- fixed issue when some metadata keys of a :class:`~data.core.readers.numpy_list.NumpyFieldList` did not match the actual field values. These metadata keys are now not available on a ``NumpyFieldList``.
