.. _data-object:

Data objects
=================

.. warning::
   This guide is currently under construction and may be incomplete or inaccurate.


Methods :func:`from_source` and :func:`from_object` return a :py:class:`Data <earthkit.data.data.Data>` object. This only provides some basic information about the data and its primary goal is to allow conversions to suitable representations for further work. The actual data loading is deferred as much as possible, until the data is converted into a given type.

The list of available conversion types can be checked with the :py:attr:`available_types <earthkit.data.data.Data.available_types>` property of the returned object. Then conversions can be performed by calling any of the corresponding ``to_*`` methods to convert the data to the desired type. E.g. to convert GRIB data to a fieldlist we can do:

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> data = ekd.from_source("file", "test6.grib")
    >>> data.available_types
    ['fieldlist', 'xarray', 'pandas', 'numpy', 'array']
    # to convert to a fieldlist
    >>> fl = data.to_fieldlist()


Data object returned by from_source
-------------------------------------

File input
++++++++++++

When :func:`from_source` reads a file input (can be data on disk, URL or memory or from a remote service) one of the following objects is returned:

.. list-table:: Types related to file formats
   :header-rows: 1
   :widths: 30 70

   * - Input data type
     - Resulting data object
   * - GRIB
     - :py:class:`earthkit.data.data.grib.GribData`
   * - NetCDF
     - :py:class:`earthkit.data.data.netcdf.NetCDFData`
   * - BUFR
     - :py:class:`earthkit.data.data.bufr.BUFRData`
   * - CSV
     - :py:class:`earthkit.data.data.csv.CSVData`
   * - ODB
     - :py:class:`earthkit.data.data.odb.ODBData`
   * - Zarr
     - :py:class:`earthkit.data.data.zarr.ZarrData`
   * - GeoJSON
     - :py:class:`earthkit.data.data.geojson.GeoJsonData`
   * - Shapefile
     - :py:class:`earthkit.data.data.shapefile.ShapeFileData`
   * - GeoTIFF
     - :py:class:`earthkit.data.data.geotiff.GeoTIFFData`
   * - CovJSON
     - :py:class:`earthkit.data.data.covjson.CovJsonData`
   * - PP (UK Met Office)
     - :py:class:`earthkit.data.data.pp.PPData`
   * - Text
     - :py:class:`earthkit.data.data.text.TextData`
   * - Unknown
     - :py:class:`earthkit.data.data.unknown.UnknownData`
   * - Hive file pattern
     - :py:class:`earthkit.data.data.hive.HiveFilePatternData`

Streams
++++++++++++

When the data is read as a :ref:`stream <streams>` with :func:`from_source` one of the following objects is returned:


.. list-table:: Types related to file formats
   :header-rows: 1
   :widths: 30 70

   * - Input data type
     - Resulting data object
   * - GRIB
     - :py:class:`earthkit.data.data.stream.StreamFieldListData`
   * - CovJSON
     - :py:class:`earthkit.data.data.stream.StreamFeatureListData`


To access the stream we need to convert the data into a stream fieldlist (GRIB) with :py:func:`to_fieldlist <earthkit.data.data.stream.StreamFieldListData.to_fieldlist>` or a stream featurelist (CovJSON) with :py:func:`to_featurelist <earthkit.data.data.stream.StreamFeatureListData.to_featurelist>`. Then we can use the resulting object to iterate through the stream once.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> url = "https://sites.ecmwf.int/repository/earthkit-data/how-tos/test4.grib"
    >>> ds = ekd.from_source("url", url, stream=True)
    >>> fl = ds.to_fieldlist()
    >>> for f in fl:
    ...     print(f)
    ...
    Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
    Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
    Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
    Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)


Examples
////////////////

    - :ref:`/how-tos/source/data_from_stream.ipynb`
    - :ref:`/how-tos/source/file_stream.ipynb`
    - :ref:`/how-tos/source/fdb.ipynb`
    - :ref:`/how-tos/source/url_stream.ipynb`


Special cases
++++++++++++++++++++++++++++++++++++

There a complex cases with mixed input data types when the returned object might be one of the following:

.. list-table:: earthkit.data API
   :header-rows: 1
   :widths: 30 70

   * - Resulting data object
     - Notes
   * - :py:class:`earthkit.data.data.multi.MultiData`
     -
   * - :py:class:`earthkit.data.data.fieldlist.FieldListData`
     -
   * - :py:class:`earthkit.data.data.featurelist.FeatureListData`
     -


Data object returned by from_object
-------------------------------------

The method :func:`from_object` is used to turn a Python object into an earthkit Data :py:class:`Data <earthkit.data.data.Data>` object. When it is called
with an earthkit-data object it returns the object itself. Otherwise, it returns the following objects depending on the input:


.. list-table:: Types supported by from_object
   :header-rows: 1
   :widths: 30 70

   * - Input type
     - Resulting data object
   * - Xarray Dataset
     - :py:class:`earthkit.data.data.wrappers.xarray.XarrayDatasetData`
   * - Xarray DataArray
     - :py:class:`earthkit.data.data.wrappers.xarray.XarrayDataArrayData`
   * - Pandas DataFrame
     - :py:class:`earthkit.data.data.wrappers.pandas.PandasDataFrameData`
   * - Pandas Series
     - :py:class:`earthkit.data.data.wrappers.pandas.PandasSeriesData`
   * - Geopandas GeoDataFrame
     - :py:class:`earthkit.data.data.wrappers.pandas.GeoPandasDataFrameData`
   * - Numpy array
     - :py:class:`earthkit.data.data.wrappers.ndarray.NumpyNDArrayData`
   * - Int value
     - :py:class:`earthkit.data.data.wrappers.integer.IntData`
   * - Float value
     - :py:class:`earthkit.data.data.wrappers.float.FloatData`
   * - String value
     - :py:class:`earthkit.data.data.wrappers.string.StrData`
