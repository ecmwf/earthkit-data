Version 0.7 Updates
/////////////////////////

Version 0.7.0
===============

Installation
++++++++++++

- made some Python dependencies optional when installing from PyPI. See details :ref:`here <install>`. Please note that by default only a minimum set of dependencies are installed.


New features
++++++++++++++++

- implemented the :ref:`parts <parts>` option for :ref:`file <data-sources-file>` sources with :ref:`grib` and :ref:`bufr` data
- added shapefile support. See the :ref:`/examples/shapefile.ipynb` notebook example.
- added the :ref:`data-sources-opendap` source to access NetCDF data from OPEnDAP services. See the :ref:`/examples/netcdf_opendap.ipynb` notebook example.
- added the :ref:`data-sources-sample` source to access data used in tests and examples
- added the ``array_backend`` option for :class:`~data.core.fieldlist.FieldList`\ s to allow specifying other array backends than numpy. Also added the :meth:`FieldList.array() <data.core.fieldlist.FieldList.array>` and :meth:`Field.array() <data.core.fieldlist.Field.array>` methods to extract the values using the given array backend. See the :ref:`/examples/grib_array_backends.ipynb` notebook example.
- added support for Lambert Conformal projection when using :meth:`Field.projection() <data.core.fieldlist.Field.projection>`
- changed the default of the ``bits_per_value`` option to None in :meth:`NumpyFieldList.save() <data.sources.numpy_list.NumpyFieldList.save>`. None means the original ``bits_per_value`` in the GRIB header is kept when the data is written to disk.
- added the ``model`` option to the :ref:`data-sources-eod` source
- added the ``prompt`` optional argument to certain retrievals to control whether the prompt is to be used. When enabled (default), the prompt asks the user to provide credentials when none seems to be specified. See the :ref:`data-sources-cds`, :ref:`data-sources-mars`, :ref:`data-sources-wekeo`, :ref:`data-sources-wekeocds` sources for more information on how the prompt works.
- added the ``user_email`` and ``user_key`` options to the :ref:`data-sources-polytope` source. This source does not use the prompt any longer.
- allowed using :func:`save` without specifying a file name. In this case an attempt is made to generate the filename automatically, when it fails an exception is thrown.
- :func:`from_source` now fails when trying to load an empty file
- removed the geo submodule. This functionality, including the :func:`nearest_point_haversine` and :func:`nearest_point_haversine` methods, is now available in the :xref:`earthkit-geo` package
- when NetCDF read as a :ref:`file source <data-sources-file>` is written to disk with :func:`save` no implicit conversion to xarray is performed on the data


Fixes
++++++

- Fixed issue when cache database entries were not added for cache files created with the force option
- Fixed issue when :ref:`data-sources-cds` retrievals failed with Python 3.8
- Fixed split_on option for :ref:`data-sources-cds` retrievals
