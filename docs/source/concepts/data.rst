.. _data-object:

Data objects
=================

Methods :func:`from_source` and :func:`from_object` return a :py:class:`Data <earthkit.data.data.Data>` object, never the lower-level ``Source`` or ``Reader`` object that actually accessed the input (see :ref:`mergers` for how the two relate for sources combining several inputs). A ``Data`` object only provides some basic information about the data and its primary goal is to allow conversions to suitable representations for further work. The actual data loading is deferred as much as possible, until the data is converted into a given type.

The list of available conversion types can be checked with the :py:attr:`available_types <earthkit.data.data.Data.available_types>` property of the returned object. Then conversions can be performed by calling any of the corresponding ``to_*`` methods to convert the data to the desired type. E.g. to convert GRIB data to a fieldlist we can do:

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> data = ekd.from_source("file", "test6.grib")
    >>> data.available_types
    ['fieldlist', 'xarray', 'pandas', 'numpy', 'array']
    # to convert to a fieldlist
    >>> fl = data.to_fieldlist()

The ``Data`` interface
-------------------------

Every ``Data`` object provides the following common properties and methods, regardless of what kind of
input produced it:

- :py:attr:`available_types <earthkit.data.data.Data.available_types>`: the list of type names the object can be converted to, e.g. ``["fieldlist", "xarray", "pandas", "numpy", "array"]``. An empty list means no conversion is currently possible (see :py:class:`~earthkit.data.data.unknown.UnknownData` and :py:class:`~earthkit.data.data.empty.EmptyData` below).
- :py:func:`is_stream() <earthkit.data.data.Data.is_stream>`: whether the object represents a :ref:`stream <streams>` rather than data already resolved to files or memory.
- :py:func:`describe() <earthkit.data.data.Data.describe>`: a human-readable description of the data.
- :py:attr:`path <earthkit.data.data.Data.path>`: the path(s) the data was read from, when applicable (``None`` for data that was not read from a file, e.g. in-memory or empty data).
- :py:func:`to(to_type, ...) <earthkit.data.data.Data.to>`: a generic conversion entry point, dispatching to the matching ``to_<to_type>`` method (or, when ``to_type`` is itself a supported input rather than a string, to the conversion inferred from its type).
- The individual ``to_*`` conversion methods themselves: :py:func:`to_fieldlist() <earthkit.data.data.Data.to_fieldlist>`, :py:func:`to_xarray() <earthkit.data.data.Data.to_xarray>`, :py:func:`to_pandas() <earthkit.data.data.Data.to_pandas>`, :py:func:`to_geopandas() <earthkit.data.data.Data.to_geopandas>`, :py:func:`to_featurelist() <earthkit.data.data.Data.to_featurelist>`, :py:func:`to_numpy() <earthkit.data.data.Data.to_numpy>` and :py:func:`to_array() <earthkit.data.data.Data.to_array>`. Calling one that is not listed in ``available_types`` raises ``NotImplementedError``.

Most concrete ``Data`` classes are implemented via :py:class:`~earthkit.data.data.SimpleData`, a base class that fills in sensible defaults for ``is_stream()`` (``False``) and ``to()`` (dispatch to the matching ``to_*`` method), leaving only the type-specific conversions to be implemented.


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
    >>> url = "https://sites.ecmwf.int/repository/earthkit-data/tutorials/test4.grib"
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

    - :ref:`/tutorials/source/data_from_stream.ipynb`
    - :ref:`/tutorials/source/file_stream.ipynb`
    - :ref:`/tutorials/source/fdb.ipynb`
    - :ref:`/tutorials/source/url_stream.ipynb`


Special cases
++++++++++++++++++++++++++++++++++++

There a complex cases with mixed input data types when the returned object might be one of the following:

:py:class:`earthkit.data.data.multi.MultiData`
    Returned when :func:`from_source` combines several inputs (e.g. a list of files) that cannot be merged
    into a single, type-specific ``Data`` object -- either because they are of different types, or because
    ``merger=False`` was requested. Wraps the underlying sources and forwards conversions to them. See
    :ref:`mergers` for details.

:py:class:`earthkit.data.data.fieldlist.FieldListData`
    Returned when a source already directly exposes a :ref:`fieldlist <fieldlist_concept>` rather than one
    of the specific file formats above, e.g. the ``list-of-dicts`` source, or an indexed/simple fieldlist
    source.

:py:class:`earthkit.data.data.featurelist.FeatureListData`
    The equivalent of ``FieldListData`` for sources exposing a featurelist directly, e.g. certain
    feature-based BUFR reads.

:py:class:`earthkit.data.data.empty.EmptyData`
    Returned in two situations:

    - :func:`from_source` is given several inputs, none of which could be read into usable data (e.g. all
      of them are of an unrecognised/unsupported format). To keep the individual input paths accessible
      instead of collapsing to an ``EmptyData``, pass ``merger=False`` (see :ref:`mergers`), which returns
      a ``MultiData`` exposing ``path`` as the list of the individual (ignored) paths.
    - A single input resolves to an **empty file** (0 bytes). This is normally an error (an
      ``EmptyFileError`` is raised), but some retrieval-based sources (e.g. :ref:`data-sources-mars`)
      explicitly allow it when the request declares ``expect="any"``, acknowledging that the request may
      legitimately return no data.

    In both cases ``available_types`` is ``["fieldlist"]``, ``to_fieldlist()`` yields an empty fieldlist,
    and ``path`` is ``None`` (the individual input path(s), if any, are not retained).


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
