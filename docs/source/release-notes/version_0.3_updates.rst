Version 0.3 Updates
/////////////////////////

Version 0.3.1
===============

Fixes
++++++

- fixed issue when could not read data from an "fdb" source


Version 0.3.0
===============

New features
++++++++++++++++

- added new source :ref:`data-sources-ads` to retrieve data from the `Copernicus Atmosphere Data Store <https://ads.atmosphere.copernicus.eu/>`_ (ADS). See the :ref:`/how-tos/source/ads.ipynb` notebook example.
- added pandas and geopandas support. See the :ref:`/how-tos/other/pandas.ipynb` notebook example.
- added :ref:`caching` policies. See the :ref:`/how-tos/misc/cache.ipynb` and :ref:`/how-tos/misc/config.ipynb` notebook examples.
- changed the return type of :meth:`~earthkit.data.core.fieldlist.FieldList.data`, which now returns an ndarray. Previously it returned a tuple of ndarrays. See the :ref:`/how-tos/grib/grib_lat_lon_value_ll.ipynb` notebook example.
- added :meth:`~earthkit.data.core.fieldlist.FieldList.data` method to :class:`~earthkit.data.core.fieldlist.FieldList`. See the :ref:`/how-tos/grib/grib_lat_lon_value_ll.ipynb` notebook example.
- added the ``valid_datetime`` metadata key, which can be used in :meth:`Field.metadata() <earthkit.data.core.fieldlist.Field.metadata>` and :class:`~earthkit.data.core.fieldlist.FieldList` methods like :meth:`~earthkit.data.core.fieldlist.FieldList.metadata`, :meth:`~earthkit.data.core.fieldlist.FieldList.sel` and  :meth:`~earthkit.data.core.fieldlist.FieldList.order_by` etc. It is particularly useful for GRIB data because the this piece of information was previously only available as two separate keys (``validityDate`` and ``validityTime``).

  .. code-block:: python

      >>> import earthkit.data
      >>> ds = earthkit.data.from_source("file", "docs/how-tos/test.grib")
      >>> ds[0].metadata("validityDate")
      20200513
      >>> ds[0].metadata("validityTime")
      1200
      >>> ds[0].metadata("valid_datetime")
      datetime.datetime(2020, 5, 13, 12, 0)

- implemented FieldList for NetCDF data. See the :ref:`/how-tos/netcdf/netcdf_fieldlist.ipynb` example.
- added experimental Metadata handling. See the :ref:`/how-tos/legacy/metadata.ipynb` example.
- added experimental input transformer tools for earthkit subpackages. It uses type-setting, or explicit mapping, to try to ensure that the inputs passed to a function are converted to the appropriate type for that method. This means that earthkit users do not have to worry about the format of their data.


Fixes
++++++

- fixed issue when cache initialisation hanged when log level was set to debug.
