
.. _api:

API reference guide
////////////////////

.. warning::
   The API reference guide is currently under construction and may be incomplete or inaccurate.

Fields
-------


- :py:class:`earthkit.data.core.field.Field`
- :py:class:`earthkit.data.core.fieldlist.FieldList`
- :py:class:`earthkit.data.indexing.indexed.IndexFieldListBase`

Metadata
----------

- :py:class:`earthkit.data.core.metadata.Metadata`
- :py:class:`earthkit.data.core.metadata.RawMetadata`
- :py:class:`earthkit.data.readers.grib.metadata.GribMetadata`
- :py:class:`earthkit.data.readers.grib.metadata.GribFieldMetadata`
- :py:class:`earthkit.data.readers.grib.metadata.StandAloneGribMetadata`

Numpy fields
---------------
- :py:class:`earthkit.data.sources.numpy_list.NumpyField`
- :py:class:`earthkit.data.sources.numpy_list.NumpyFieldList`

GRIB
-------

- :py:class:`earthkit.data.readers.grib.index.GribFieldList`
- :py:class:`earthkit.data.readers.grib.codes.GribField`

BUFR
-----

- :py:class:`earthkit.data.readers.bufr.bufr.BUFRList`
- :py:class:`earthkit.data.readers.bufr.bufr.BUFRMessage`

CSV
----

- :py:class:`earthkit.data.readers.csv.CSVReader`


Encoders
---------

- :py:class:`earthkit.data.encoders.encoder.Encoder`
- :py:class:`earthkit.data.encoders.grib.GribEncoder`
- :py:class:`earthkit.data.encoders.netcdf.NetCDFEncoder`
- :py:class:`earthkit.data.encoders.geotiff.GeoTiffEncoder`
- :py:class:`earthkit.data.encoders.csv.CSVEncoder`


Targets
---------

- :py:class:`earthkit.data.targets.target.Target`
- :py:class:`earthkit.data.targets.file.FileTarget`
- :py:class:`earthkit.data.targets.file.FilePatternTarget`
- :py:class:`earthkit.data.targets.fdb.FdbTarget`

Xarray engine
--------------
- :py:class:`earthkit.data.xr_engine.engine.EarthkitBackendEntrypoint`

Other
--------

- :py:class:`earthkit.data.utils.bbox.BoundingBox`
