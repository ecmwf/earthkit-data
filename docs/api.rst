
.. _api:

API reference guide
////////////////////

.. warning::
   The API reference guide is currently under construction and may be incomplete or inaccurate.

Fields
-------

- :py:class:`earthkit.data.core.field.Field`
- :py:class:`earthkit.data.core.fieldlist.FieldList`

Data
------

- :py:class:`earthkit.data.data.Data`
- :py:class:`earthkit.data.data.SimpleData`

GRIB
-------

- :py:class:`~data.readers.grib.index.GribFieldList`
- :py:class:`~data.readers.grib.codes.GribField`

BUFR
-----

- :py:class:`~data.readers.bufr.bufr.BUFRList`
- :py:class:`~data.readers.bufr.bufr.BUFRMessage`

CSV
----

- :py:class:`~data.readers.csv.CSVReader`


Encoders
---------

- :py:class:`~data.encoders.encoder.Encoder`
- :py:class:`~data.encoders.grib.GribEncoder`
- :py:class:`~data.encoders.netcdf.NetCDFEncoder`
- :py:class:`~data.encoders.geotiff.GeoTiffEncoder`
- :py:class:`~data.encoders.csv.CSVEncoder`


Targets
---------

- :py:class:`~data.targets.target.Target`
- :py:class:`~data.targets.file.FileTarget`
- :py:class:`~data.targets.file.FilePatternTarget`
- :py:class:`~data.targets.fdb.FdbTarget`

Xarray engine
--------------
- :py:class:`~data.xr_engine.engine.EarthkitBackendEntrypoint`

Other
--------

- :py:class:`~data.utils.bbox.BoundingBox`
