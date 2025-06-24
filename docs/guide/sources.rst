.. _data-sources:

Data sources
===============

Getting data from a source
----------------------------

We can get data from a given source by using :func:`from_source`:

.. py:function:: from_source(name, *args, **kwargs)

  Return a :ref:`data object <data-object>` from the source specified by ``name`` .

  :param str name: the source (see below)
  :param tuple *args: specifies the data location and additional parameters to access the data
  :param dict **kwargs: provides **additional functionalities** including caching, filtering, sorting and indexing

  **earthkit-data** has the following built-in sources:

  .. list-table:: Data sources
    :widths: 30 70
    :header-rows: 1

    * - Name
      - Description
    * - :ref:`data-sources-file`
      - read data from a file/files
    * - :ref:`data-sources-file-pattern`
      - read data from a list of files  created from a pattern
    * - :ref:`data-sources-url`
      - read data from a URL
    * - :ref:`data-sources-url-pattern`
      - read data from a list of URLs created from a pattern
    * - :ref:`data-sources-sample`
      - read example data
    * - :ref:`data-sources-stream`
      - read data from a stream
    * - :ref:`data-sources-memory`
      - read data from a memory buffer
    * - :ref:`data-sources-forcings`
      - generate forcing data
    * - :ref:`data-sources-lod`
      - read data from a list of dictionaries
    * - :ref:`data-sources-multi`
      - read data from multiple sources
    * - :ref:`data-sources-ads`
      - retrieve data from the `Copernicus Atmosphere Data Store <https://ads.atmosphere.copernicus.eu/>`_ (ADS)
    * - :ref:`data-sources-cds`
      - retrieve data from the `Copernicus Climate Data Store <https://cds.climate.copernicus.eu/>`_ (CDS)
    * - :ref:`data-sources-ecfs`
      - retrieve data from the ECMWF `ECFS File Storage system <https://confluence.ecmwf.int/display/UDOC/ECFS+user+documentation>`_
    * - :ref:`data-sources-eod`
      - retrieve `ECMWF open data <https://www.ecmwf.int/en/forecasts/datasets/open-data>`_
    * - :ref:`data-sources-fdb`
      - retrieve data from the `Fields DataBase <https://fields-database.readthedocs.io/en/latest/>`_ (FDB)
    * - :ref:`data-sources-mars`
      - retrieve data from the ECMWF `MARS archive <https://confluence.ecmwf.int/display/UDOC/MARS+user+documentation>`_
    * - :ref:`data-sources-opendap`
      - retrieve NetCDF data from `OPEnDAP <https://en.wikipedia.org/wiki/OPeNDAP>`_ services
    * - :ref:`data-sources-polytope`
      - retrieve fields from the `Polytope services <https://polytope.readthedocs.io/en/latest/>`_
    * - :ref:`data-sources-s3`
      - retrieve data from Amazon S3 buckets
    * - :ref:`data-sources-wekeo`
      - retrieve data from `WEkEO`_ using the WEkEO grammar
    * - :ref:`data-sources-wekeocds`
      - retrieve `CDS <https://cds.climate.copernicus.eu/>`_ data stored on `WEkEO`_ using the `cdsapi`_ grammar
    * - :ref:`data-sources-zarr`
      - load data from a `Zarr <https://zarr.readthedocs.io/en/stable/>`_ store

----------------------------------

.. _data-sources-file:

file
----

.. py:function:: from_source("file", path, expand_user=True, expand_vars=False, unix_glob=True, recursive_glob=True, filter=None, parts=None)
  :noindex:

  The simplest source is ``file``, which can access a local file/list of files.

  :param path: input path(s). Each path can be a file path or a directory path. If it is a directory path, it is recursively scanned for supported files. When a path is an archive format such as ``.zip``, ``.tar``, ``.tar.gz``, etc, *earthkit-data* will attempt to open it and extract any usable files, which are then stored in the :ref:`cache <caching>`. Each filepath can contain the :ref:`parts <parts>` defining the byte ranges to read.
  :type path: str, list, tuple
  :param bool expand_user: replace the leading ~ or ~user in ``path`` by that user's home directory. See ``os.path.expanduser``
  :param bool expand_vars:  expand shell environment variables in ``path``. See ``os.path.expandpath``
  :param bool unix_glob: allow UNIX globbing in ``path``
  :param bool recursive_glob: allow recursive scanning of directories. Only used when ``uxix_glob`` is True
  :param filter: apply filter to the files read from directories or archives. The filter can be a callable or a string. If it is a string, it is interpreted as a UNIX glob pattern. If it is a callable, it should accept the full file path as a string and return a boolean.
  :type filter: str, callable
  :param parts: the :ref:`parts <parts>` to read from the file(s) specified by ``path``. Cannot be used when ``path`` already defines the :ref:`parts <parts>`.
  :type parts: pair, list or tuple of pairs, None
  :param bool stream: if ``True``, the data is read as a :ref:`stream <streams>`. Directories and archives are supported. Stream based access is only available for :ref:`grib` and CoverageJson data. See details about streams :ref:`here <streams>`. *New in version 0.11.0*
  :param bool read_all: if ``True``, all the data is read straight to memory from a :ref:`stream <streams>`. Used when ``stream=True``. *New in version 0.11.0*

  *earthkit-data* will inspect the content of the files to check for any of the
  supported :ref:`data formats <data-format>`.

  When the input is an archive format such as ``.zip``, ``.tar``, ``.tar.gz``, etc,
  *earthkit-data* will attempt to open it and extract any usable files, which are then stored in the :ref:`cache <caching>`.

  The ``path`` can be used in a flexible way:

  .. code:: python

      import earthkit.data as ekd

      # UNIX globbing is allowed by default
      ds = ekd.from_source("file", "path/to/t_*.grib")

      # list of files can be specified
      ds = ekd.from_source("file", ["path/to/f1.grib", "path/to/f2.grib"])

      # a path can be a directory, in this case it is recursively scanned for supported files
      ds = ekd.from_source("file", "path/to/dir")


  The following examples using parts:

  .. code:: python

      import earthkit.data as ekd

      # reading only certain parts (byte ranges) from a single file
      ds = ekd.from_source("file", "my.grib", parts=[(0, 150), (400, 160)])

      # reading only certain parts (byte ranges) from multiple files
      ds = ekd.from_source(
          "file",
          [
              ("a.grib", (0, 150)),
              ("b.grib", (240, 120)),
              ("c.grib", None),
              ("d.grib", [(240, 120), (720, 120)]),
          ],
      )



  Further examples:

    - :ref:`/examples/files.ipynb`
    - :ref:`/examples/multi_files.ipynb`
    - :ref:`/examples/file_parts.ipynb`
    - :ref:`/examples/file_stream.ipynb`
    - :ref:`/examples/tar_files.ipynb`
    - :ref:`/examples/grib_overview.ipynb`
    - :ref:`/examples/bufr_temp.ipynb`
    - :ref:`/examples/netcdf.ipynb`
    - :ref:`/examples/odb.ipynb`

.. _data-sources-file-pattern:

file-pattern
--------------

.. py:function:: from_source("file-pattern", pattern, *args, hive_partitioning=False, **kwargs)
  :noindex:

  The ``file-pattern`` source reads data from paths specified by a :ref:`pattern <patterns>`.

  :param pattern: input path pattern using ``{}`` brackets to define parameters that can be substituted. See :ref:`patterns <patterns>` for details.
  :type pattern: str
  :param tuple *args: specify the values to substitute into the parameters ``pattern``. Each parameter can be a list/tuple or a single value.
  :param hive_partitioning: control how the ``pattern`` is interpreted. See details below.
  :type hive_partitioning: bool
  :param dict **kwargs: other keyword arguments specifying the parameter values

  The actual behaviour and the type of the returned object depend on ``hive_partitioning``:

hive_partioning=False
////////////////////////////

  When ``hive_partitioning`` is ``False``, first, the pattern parameters are substituted with the values specified by the ``*args`` and ``**kwargs``, see :ref:`patterns <patterns>` for details. For this, all the possible values must be specified for each pattern parameter. Next, the paths are constructed by taking the Cartesian product of the substituted values. Finally, the resulting paths are read and :ref:`from_source <data-sources-file-pattern>` returns a single object (for GRIB data it will be a :py:class:`Fieldlist`).

    .. code-block:: python

        import datetime
        import earthkit.data as ekd

        # ds is a fieldlist
        ds = ekd.from_source(
            "file-pattern",
            "path/to/data-{my_date:date(%Y-%m-%d)}-{run_time}-{param}.grib",
            {
                "my_date": datetime.datetime(2020, 5, 2),
                "run_time": [12, 18],
                "param": ["t2", "msl"],
            },
        )


    The code above substitutes "my_date", "run_time" and "param" into the ``pattern`` and constructs the following file paths read into single GRIB :py:class:`Fieldlist`::

        path/to/data-2020-05-02-12-t2.grib
        path/to/data-2020-05-02-12-msl.grib
        path/to/data-2020-05-02-18-t2.grib
        path/to/data-2020-05-02-18-msl.grib


.. _file-pattern-hive-partioning:

hive_partioning=True
/////////////////////////////

    When ``hive_partitioning`` is ``True``, the ``pattern`` defines a Hive partitioning with each pattern parameter interpreted as a metadata key. The returned object has a limited scope only supporting the :meth:`sel` method. Calling any of these methods will trigger a filesystem scan for all the matching files. During this scan, if the required metadata is present in the pattern no files will be opened at all to extract their metadata, which can be an enormous optimisation. Another advantage is that during the scan entire file system branches can be skipped based simply on inspecting the actual file path.

    Pattern values are optional, but can be still specified to restrict the search to a specific set of values.

    For the hive partitioning example below let us suppose we have the following directory structure containing several years of GRIB data:

    .. code-block:: text

        mydir/
            20230101/
                myfile_t.grib
                myfile_r.grib
                myfile_u.grib
                myfile_v.grib
            20230102/
                myfile_t.grib
                myfile_r.grib
                myfile_u.grib
                myfile_v.grib
            20230103/
                myfile_t.grib
                myfile_r.grib
                myfile_u.grib
                myfile_v.grib
            20230104/
            ...

    .. code-block:: python

        import datetime
        import earthkit.data as ekd

        # At this point nothing is scanned/read yet. ds only has the
        # sel() method.
        ds = from_source(
            "file-pattern", "mydir/{date}/myfile_{param}.grib", hive_partitioning=True
        )

        # The following line will trigger a filesystem scan
        # for all the matching files. The scan will be limited to the
        # "mydir/20230101/" sub-directory and non of the GRIB files will be
        # opened to extract their metadata. The returned object will
        # be a Fieldlist.
        ds1 = ds.sel(date="20230101", param=["t", "r"])


Further examples:

    - :ref:`/examples/files.ipynb`


.. _data-sources-url:

url
---

.. py:function:: from_source("url", url, unpack=True, parts=None, stream=False, read_all=False)
  :noindex:

  The ``url`` source will download the data from the address specified and store it in the :ref:`cache <caching>`. The supported data formats are the same as for the :ref:`file <data-sources-file>` data source above.

  :param url: the URL(s) to download. Each URL can contain the :ref:`parts <parts>` defining the byte ranges to read.
  :type url: str
  :param bool unpack: for archive formats such as ``.zip``, ``.tar``, ``.tar.gz``, etc, *earthkit-data* will attempt to open it and extract any usable file. To keep the downloaded file as is use ``unpack=False``
  :param parts: the :ref:`parts <parts>` to read from the resource(s) specified by ``url``. Cannot be used when ``url`` already defines the :ref:`parts <parts>`.
  :type parts: pair, list or tuple of pairs, None
  :param bool stream: if ``True``, the data is read as a :ref:`stream <streams>`. Otherwise the data is retrieved into a file and stored in the :ref:`cache <caching>`. This option only works for GRIB data. No archive formats supported (``unpack`` is ignored). ``stream`` only works for ``http`` and ``https`` URLs. See details about streams :ref:`here <streams>`.
  :param bool read_all: if ``True``, all the data is read straight to memory from a :ref:`stream <streams>`. Used when ``stream=True``. *New in version 0.8.0*
  :param dict **kwargs: other keyword arguments specifying the request

  .. code-block:: python

      >>> import earthkit.data as ekd
      >>> ds = ekd.from_source(
      ...     "url",
      ...     "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test4.grib",
      ... )
      >>> ds.ls()
        centre shortName    typeOfLevel  level  dataDate  dataTime stepRange dataType  number    gridType
      0   ecmf         t  isobaricInhPa    500  20070101      1200         0       an       0  regular_ll
      1   ecmf         z  isobaricInhPa    500  20070101      1200         0       an       0  regular_ll
      2   ecmf         t  isobaricInhPa    850  20070101      1200         0       an       0  regular_ll
      3   ecmf         z  isobaricInhPa    850  20070101      1200         0       an       0  regular_ll

  .. code-block:: python

      >>> import earthkit.data as ekd
      >>> ds = ekd.from_source(
      ...     "url",
      ...     "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test4.grib",
      ...     parts=[(0, 130428), (260856, 130428)],
      ... )
      >>> ds.ls()
        centre shortName    typeOfLevel  level  dataDate  dataTime stepRange dataType  number    gridType
      0   ecmf         t  isobaricInhPa    500  20070101      1200         0       an       0  regular_ll
      1   ecmf         t  isobaricInhPa    850  20070101      1200         0       an       0  regular_ll

  Further examples:

    - :ref:`/examples/url.ipynb`
    - :ref:`/examples/url_parts.ipynb`
    - :ref:`/examples/url_stream.ipynb`


.. _data-sources-url-pattern:


url-pattern
-----------

.. py:function:: from_source("url-pattern", url, unpack=True)
  :noindex:

  The ``url-pattern`` source will build urls from the pattern specified,
  using the other arguments to fill the pattern. Each argument can be a list
  to iterate and create the cartesian product of all lists.
  Then each url is downloaded and stored in the :ref:`cache <caching>`. The
  supported download the data from the address data formats are the same as
  for the *file* and *url* data sources above.

  .. code-block:: python

      import earthkit.data as ekd

      ds = ekd.from_source(
          "url-pattern",
          "https://www.example.com/data-{foo}-{bar}-{qux}.csv",
          foo=[1, 2, 3],
          bar=["a", "b"],
          qux="unique",
      )

  The code above will download and process the data from the six following urls::

    https://www.example.com/data-1-a-unique.csv
    https://www.example.com/data-2-a-unique.csv
    https://www.example.com/data-3-a-unique.csv
    https://www.example.com/data-1-b-unique.csv
    https://www.example.com/data-2-b-unique.csv
    https://www.example.com/data-3-b-unique.csv

  If the urls are pointing to archive format, the data will be unpacked by
  ``url-pattern`` according to the **unpack** argument, similarly to what
  the source ``url`` does (see above the :ref:`data-sources-url` source).



.. _data-sources-sample:

sample
------

.. py:function:: from_source("sample", name_or_path)
  :noindex:

  The ``sample`` source will download example data prepared for earthkit and store it in the :ref:`cache <caching>`. The supported data formats are the same as for the :ref:`file <data-sources-file>` data source above.

  :param name_or_path: input file name(s) or relative path(s) to the root of the remote storage folder.
  :type name_or_path: str, list, tuple

  .. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds = ekd.from_source("sample", "storm_ophelia_wind_850.grib")
    >>> ds.ls()
      centre shortName    typeOfLevel  level  dataDate  dataTime stepRange dataType  number    gridType
    0   ecmf         u  isobaricInhPa    850  20171016         0         0       an       0  regular_ll
    1   ecmf         v  isobaricInhPa    850  20171016         0         0       an       0  regular_ll



.. _data-sources-stream:

stream
--------------

.. py:function:: from_source("stream", stream, read_all=False)
  :noindex:

  The ``stream`` source will read data from a stream (or streams), which can be an FDB stream, a standard Python IO stream or any object implementing the necessary stream methods. At the moment it only works for :ref:`grib` and CoverageJson data. For more details see :ref:`here <streams>`.

  :param stream: the stream(s)
  :type stream: stream, list, tuple
  :param bool read_all: if ``True``, all the data is read into memory from a stream. Used when ``stream=True``. *New in version 0.8.0*

  In the examples below, for simplicity, we create a file stream from a :ref:`grib` file. By default :ref:`from_source() <data-sources-stream>` returns an object that can only be used as an iterator.

  .. code-block:: python

      >>> import earthkit.data as ekd
      >>> stream = open("docs/examples/test4.grib", "rb")
      >>> ds = ekd.from_source("stream", stream)

      # f is a GribField
      >>> for f in ds:
      ...     print(f)
      ...
      GribField(t,500,20070101,1200,0,0)
      GribField(z,500,20070101,1200,0,0)
      GribField(t,850,20070101,1200,0,0)
      GribField(z,850,20070101,1200,0,0)

  We can also iterate through the stream in batches of fixed size using ``batched()``:

    .. code-block:: python

      >>> import earthkit.data as ekd
      >>> stream = open("docs/examples/test4.grib", "rb")
      >>> ds = ekd.from_source("stream", stream, batch_size=2)

       # f is a FieldList
      >>> for f in ds.batched(2):
      ...     print(f"len={len(f)} {f.metadata(('param', 'level'))}")
      ...
      len=2 [('t', 500), ('z', 500)]
      len=2 [('t', 850), ('z', 850)]


  When using ``group_by()`` we can iterate through the stream in groups defined by metadata keys. In this case each iteration step yields a :obj:`FieldList <data.readers.grib.index.FieldList>`.

    .. code-block:: python

      >>> import earthkit.data as ekd
      >>> stream = open("docs/examples/test4.grib", "rb")
      >>> ds = ekd.from_source("stream", stream)

      # f is a FieldList
      >>> for f in ds.group_by("level"):
      ...     print(f"len={len(f)} {f.metadata(('param', 'level'))}")
      ...
      len=2 [('t', 500), ('z', 500)]
      len=2 [('t', 850), ('z', 850)]

  We can consume the whole stream and load all the data into memory by using ``read_all=True`` in :ref:`from_source() <data-sources-stream>`. **Use this option carefully!**

    .. code-block:: python

      >>> import earthkit.data as ekd
      >>> stream = open("docs/examples/test4.grib", "rb")
      >>> ds = ekd.from_source("stream", stream, read_all=True)

      # ds is empty at this point, but calling any method on it will
      # consume the whole stream
      >>> len(ds)
      4

      # now ds stores all the messages in memory

  See the following notebook examples for further details:

    - :ref:`/examples/data_from_stream.ipynb`
    - :ref:`/examples/fdb.ipynb`
    - :ref:`/examples/url_stream.ipynb`


.. _data-sources-memory:

memory
--------------

.. py:function:: from_source("memory", buffer)
  :noindex:

  The ``memory`` source will read data from a memory buffer. Currently it only works for a ``buffer`` storing a single :ref:`grib` message or CoverageJson data. The result is a FieldList object storing all the data in memory.

  .. code-block:: python

      import earthkit.data as ekd

      # buffer storing a GRIB message
      buffer = ...

      ds = ekd.from_source("memory", bufr)

      # f is the only GribField in ds
      f = ds[0]


  Please note that a buffer can always be read as a :ref:`stream source <data-sources-stream>` using ``io.BytesIO``. The equivalent code to the example above using a stream is:

  .. code-block:: python

      import io
      import earthkit.data as ekd

      # buffer storing a GRIB message
      buffer = ...
      stream = io.BytesIO(buffer)

      ds = ekd.from_source("stream", stream, real_all=True)

      # f is the only GribField in ds
      f = ds[0]


.. _data-sources-forcings:

forcings
--------------

.. py:function:: from_source("forcings", source_or_dataset=None, *, request={}, **kwargs)
  :noindex:

  :param source_or_dataset: the input data. It can the object returned from :py:func:`from_source` or a FieldLists. If it is None a :ref:`data-sources-lod` source is built from the ``request``. The first field in this data is used a template to build the forcing fields.
  :type source_or_dataset: Source, FieldList or None
  :param request: specify the request
  :type request: dict
  :param dict **kwargs: other keyword arguments specifying the request

  The ``forcings`` source generate forcings fields.


.. _data-sources-lod:

list-of-dicts
--------------

.. py:function:: from_source("list-of-dicts", list_of_dicts)
  :noindex:

  The ``list-of-dicts`` source will read data from a list of dictionaries. Each dictionary represents a single field and
  the result is a FieldList consisting of ArrayField fields.

  .. note::

    No attempt is made to represent the fields internally as GRIB messages, so field functionalities are limited,
    and some of them may not work at all. The fields cannot be saved to a GRIB file.

  The only **required** key for a dictionary is "values", which represents the data values. It can be a list, tuple or an ndarray.
  All the other keys define the **metadata** and are optional. However, many field functionalities require the existence
  of specific keys (see below).

  The keys that might be interpreted internally can be grouped into the following categories:

  Geography keys:

    - "latitudes": the latitudes, iterable or ndarray
    - "longitudes": the longitudes, iterable or ndarray
    - "distinctLatitudes": the distinct latitudes, iterable or ndarray
    - "distinctLongitudes": the distinct longitudes, iterable or ndarray

    These keys are required to make any geography related field functionalities work
    (e.g. :py:meth:`to_latlon`). The role of the keys depends on the grid type:

    - structured grids: "latitudes" and "longitudes" can define the distinct
      latitudes and longitudes or the full grid. The keys "distinctLatitudes" and "distinctLongitudes" are
      only used when "latitudes" and "longitudes" are not present and in this
      case they define the distinct latitudes and longitudes.
    - other grids: "latitudes" and "longitudes" must have the same number of points as "values".

    When other GRIB related geography keys are present, no attempt is made to check if they are consistent
    with the grid defined by "latitudes" and "longitudes". Therefore their usage is strongly discouraged.

    See: :ref:`/examples/list_of_dicts_geography.ipynb` for more details.

  Parameter keys:

    - "param": the parameter name, alias to "shortName" if missing. Must be a str.
    - "shortName": the parameter name, alias to "param" if missing. Must be a str.

  Temporal keys:

    - "date": the date part of the forecast reference time. Must be an int as YYYYMMDD
      (the same format as the "date" ecCodes GRIB key).
    - "time": the time part of the forecast reference time. Must be an int as hhmm with leading zeros omitted
      (the same format as the "time" ecCodes GRIB key).
    - "dataDate": alias to "date"
    - "dataTime": alias to "time"
    - "forecast_reference_time": the forecast reference time. Must be a datetime object. If not present
      it is automatically built from "date" and "time" or from "valid_datetime" and "step".
    - "base_datetime": alias to "forecast_reference_time"
    - "valid_datetime": the valid datetime. Must be a datetime object. If not present
      it is automatically built from "forecast_reference_time" and "step".
    - "step": the forecast step. If it is an int, it specifies the number of hours. If it is a str it must
      use the same format as the "step" ecCodes GRIB key. Can be a timedelta object.
    - "step_timedelta": the step timedelta. Must be a timedelta object. If not present
      it is automatically built from "step".

  Level keys:

    - "level": the level value. Must be a number.
    - "levelist": the level value. Must be a number.
    - "typeOfLevel": the type of level. Must be a str.
    - "levtype": the type of level. Must be a str.

    These keys are supposed to be the same as the corresponding GRIB keys.

  Ensemble keys:

    - "number": the ensemble member number. Must be an int.

  Other keys:

    Other keys can be used to store additional metadata.

  Further examples:

      - :ref:`/examples/fields_from_dict_in_loop.ipynb`
      - :ref:`/examples/list_of_dicts_overview.ipynb`
      - :ref:`/examples/list_of_dicts_geography.ipynb`

.. _data-sources-multi:

multi
--------------

.. py:function:: from_source("multi", *sources, merger=None, **kwargs)
  :noindex:

  The ``multi`` source reads multiple sources.

  :param tuple *sources: the sources
  :param merger: if it is None an attempt is made to merge/concatenate the sources by their classes (using the nearest common class). Otherwise the sources are merged/concatenated using the merger in a lazy way. The merger can one of the following:

    - class/object implementing  the :func:`to_xarray` or :func:`to_pandas` methods
    - callable
    - str, describing a call either to "concat" or "merge". E.g.: "concat(concat_dim=time)"
    - tuple with 2 elements. The fist element is a str, either "concat" or "merge", and the second element is a dict with the keyword arguments for the call. E.g.: ("concat", {"concat_dim": "time"})
  :param dict **kwargs: other keyword arguments



.. _data-sources-ads:

ads
---

.. py:function:: from_source("ads", dataset, *args, **kwargs)
  :noindex:

  The ``ads`` source accesses the `Copernicus Atmosphere Data Store`_ (ADS), using the cdsapi_ package.  In addition to data retrieval, the request has post-processing options such as ``grid`` and ``area`` for regridding and sub-area extraction respectively. It can
  also contain the earthkit-data specific :ref:`split_on <split_on>` parameter.

  :param str dataset: the name of the ADS dataset
  :param tuple *args: specify the request as a dict
  :param dict **kwargs: other keyword arguments specifying the request

  .. note::

    Currently, for accessing ADS earthkit-data requires the credentials for cdsapi_ to be stored in the RC file ``~/.adsapirc``.

    When no ``~/.adsapirc`` RC file exists a prompt will appear to specify the credentials for cdsapi_ and write them into ``~/.adsapirc``.


  The following example retrieves CAMS global reanalysis GRIB data for 2 parameters:

  .. code-block:: python

      import earthkit.data as ekd

      ds = ekd.from_source(
          "ads",
          "cams-global-reanalysis-eac4",
          variable=["particulate_matter_10um", "particulate_matter_1um"],
          area=[50, -50, 20, 50],  # N,W,S,E
          date="2012-12-12",
          time="12:00",
      )

  Data downloaded from the ADS is stored in the the :ref:`cache <caching>`.

  To access data from the ADS, you will need to register and retrieve an access token. The process is described `here <https://ads.atmosphere.copernicus.eu/how-to-api>`__. For more information, see the `ADS_knowledge base`_.

  Further examples:

      - :ref:`/examples/ads.ipynb`


.. _data-sources-cds:

cds
---

.. py:function:: from_source("cds", dataset, *args, prompt=True, **kwargs)
  :noindex:

  The ``cds`` source accesses the `Copernicus Climate Data Store`_ (CDS), using the cdsapi_ package. In addition to data retrieval, the request has post-processing options such as ``grid`` and ``area`` for regridding and sub-area extraction respectively. It can
  also contain the earthkit-data specific :ref:`split_on <split_on>` parameter.

  :param str dataset: the name of the CDS dataset
  :param tuple *args: specify the request as dict. A sequence of dicts can be used to specify multiple requests.
  :param bool prompt: if ``True``, it can offer a prompt to specify the credentials for cdsapi_ and write them into the default RC file ``~/.cdsapirc``. The prompt only appears when:

    - no cdsapi_ RC file exists at the default location ``~/.cdsapirc``
    - no cdsapi_ RC file exists at the location specified via the ``CDSAPI_RC`` environment variable
    - no credentials specified via the ``CDSAPI_URL`` and ``CDSAPI_KEY`` environment variables
  :param dict **kwargs: other keyword arguments specifying the request

  The following example retrieves ERA5 reanalysis GRIB data for a subarea for 2 surface parameters. The request is specified using ``kwargs``:

  .. code-block:: python

      import earthkit.data as ekd

      ds = ekd.from_source(
          "cds",
          "reanalysis-era5-single-levels",
          variable=["2t", "msl"],
          product_type="reanalysis",
          area=[50, -10, 40, 10],  # N,W,S,E
          grid=[2, 2],
          date="2012-05-10",
      )

  The same retrieval can be defined by passing the request as a positional argument:

  .. code-block:: python

      import earthkit.data as ekd

      req = dict(
          variable=["2t", "msl"],
          product_type="reanalysis",
          area=[50, -10, 40, 10],  # N,W,S,E
          grid=[2, 2],
          date="2012-05-10",
      )

      ds = ekd.from_source(
          "cds",
          "reanalysis-era5-single-levels",
          req,
      )


  Data downloaded from the CDS is stored in the the :ref:`cache <caching>`.

  To access data from the CDS, you will need to register and retrieve an access token. The process is described `here <https://cds.climate.copernicus.eu/how-to-api>`__. For more information, see the `CDS_knowledge base`_.

  Further examples:

      - :ref:`/examples/cds.ipynb`


.. _data-sources-ecfs:

ecfs
-------------------

.. py:function:: from_source("ecfs", path)
  :noindex:

  The ``ecfs`` source provides access to `ECMWF's File Storage system <https://confluence.ecmwf.int/display/UDOC/ECFS+user+documentation>`_. This service is only available at ECMWF.

  The ``path`` has to start with ``ec:`` followed by the path to the file to retrieve.


.. _data-sources-eod:

ecmwf-open-data
-------------------

.. py:function:: from_source("ecmwf-open-data", *args, source="ecmwf", model="ifs", **kwargs)
  :noindex:

  The ``ecmwf-open-data`` source provides access to the `ECMWF open data`_, which is a subset of ECMWF real-time forecast data made available to the public free of charge.  It uses the `ecmwf-opendata <https://github.com/ecmwf/ecmwf-opendata>`_ package.

  :param tuple *args: specify the request as a dict
  :param str source: either the name of the server to contact or a fully qualified URL. Possible values are "ecmwf" to access ECMWF's servers, or "azure" to access data hosted on Microsoft's Azure. Default is "ecmwf".
  :param str model: name of the model that produced the data. Use "ifs" for the physics-driven model and "aifs" for the data-driven model. Please note that "aifs" is currently experimental and only produces a small subset of fields. Default is "ifs".
  :param dict **kwargs: other keyword arguments specifying the request

  Details about the request format can be found `here <https://github.com/ecmwf/ecmwf-opendata>`__.

  The following example retrieves forecast for 2 surface parameters from the latest forecast:

  .. code-block:: python

      import earthkit.data

      ds = earthkit.data.from_source(
          "ecmwf-open-data", param=["2t", "msl"], levtype="sfc", step=[0, 6, 12]
      )


  The resulting GRIB data files are stored in the :ref:`cache <caching>`.

  Further examples:

      - :ref:`/examples/ecmwf_open_data.ipynb`


.. _data-sources-fdb:

fdb
---

.. py:function:: from_source("fdb", *args, config=None, userconfig=None, stream=True, read_all=False, lazy=False, **kwargs)
  :noindex:

  The ``fdb`` source accesses the `FDB (Fields DataBase) <https://fields-database.readthedocs.io/en/latest/>`_, which is a domain-specific object store developed at ECMWF for storing, indexing and retrieving GRIB data. earthkit-data uses the `pyfdb <https://pyfdb.readthedocs.io/en/latest>`_ package to retrieve data from FDB.

  :param tuple *args: positional arguments specifying the request as a dict
  :param dict,str config: the FDB configuration directly passed to ``pyfdb.FDB()``. If not provided, the configuration is either read from the environment or the default configuration is used. *New in version 0.11.0*
  :param dict,str userconfig: the FDB user configuration directly passed to ``pyfdb.FDB()``. If not provided, the configuration is either read from the environment or the default configuration is used. *New in version 0.11.0*
  :param bool stream: if ``True``, the data is read as a :ref:`stream <streams>`. Otherwise it is retrieved into a file and stored in the :ref:`cache <caching>`. Stream-based access only works for :ref:`grib` and CoverageJson data. See details about streams :ref:`here <streams>`.
  :param bool read_all: if ``True``, all the data is read into memory from a :ref:`stream <streams>`. Used when ``stream=True``. *New in version 0.8.0*
  :param bool lazy: if ``True``, the data is read in a lazy way. This means the following:

    - GRIB data is not retrieved until it is explicitly/implictly requested for a given field
    - metadata related calls (e.g. :func:`metadata` or :func:`sel`) work without retrieving the GRIB data
    - :meth:`~data.core.fieldlist.FieldList.to_xarray` works without retrieving the GRIB data
    - the retrieved GRIB data is not cached (either in memory or on disk) but gets deleted as soon as the data values are extracted. Repeated request for the data values will trigger a new retrieval.
    - the resulting :py:class:`FieldList` always retrives one GRIB field as a reference and stores it in memory throughout the lifetime of the :py:class:`FieldList`. This is managed internally.

    When ``lazy=True`` the ``stream`` and ``read_all`` options are ignored. Please note that this is an **experimental** feature. *New in version 0.14.0*
  :param dict **kwargs: other keyword arguments specifying the request

  The following example retrieves analysis :ref:`grib` data for 3 surface parameters as stream.
  By default we will consume one message at a time and ``ds`` can only be used as an iterator:

  .. code-block:: python

      >>> import earthkit.data as ekd
      >>> request = {
      ...     "class": "od",
      ...     "expver": "0001",
      ...     "stream": "oper",
      ...     "date": "20240421",
      ...     "time": [0, 12],
      ...     "domain": "g",
      ...     "type": "an",
      ...     "levtype": "sfc",
      ...     "step": 0,
      ...     "param": [151, 167, 168],
      ... }
      >>>
      >>> ds = ekd.from_source("fdb", request)
      >>> for f in ds:
      ...     print(f)
      ...
      GribField(msl,None,20240421,0,0,0)
      GribField(2t,None,20240421,0,0,0)
      GribField(2d,None,20240421,0,0,0)
      GribField(msl,None,20240421,1200,0,0)
      GribField(2t,None,20240421,1200,0,0)
      GribField(2d,None,20240421,1200,0,0)

  We can also iterate through the stream in batches of fixed size using ``batched``:

  .. code-block:: python

      >>> ds = ekd.from_source("fdb", request)
      >>> for f in ds.batched(2):
      ...     print(f"len={len(f)} {f.metadata(('param', 'level'))}")
      ...
      len=2 [('msl', 0), ('2t', 0)]
      len=2 [('2d', 0), ('msl', 0)]
      len=2 [('2t', 0), ('2d', 0)]

  We can use ``batch_size=2`` to read 2 fields at a time. ``ds`` is still just an iterator, but ``f`` is now a :obj:`FieldList <data.readers.grib.index.FieldList>` containing 2 fields:

  When using ``group_by()`` we can iterate through the stream in groups defined by metadata keys. In this case each iteration step yields a :obj:`FieldList <data.readers.grib.index.FieldList>`.

  .. code-block:: python

      >>> ds = ekd.from_source("fdb", request)
      >>> for f in ds.group_by("time"):
      ...     print(f"len={len(f)} {f.metadata(('param', 'level'))}")
      ...
      len=3 [('msl', 0), ('2t', 0), ('2d', 0)]
      len=3 [('msl', 0), ('2t', 0), ('2d', 0)]

  We can consume the whole stream and load all the data into memory by using ``read_all=True`` in :ref:`from_source() <data-sources-stream>`. **Use this option carefully!**

  .. code-block:: python

      >>> import earthkit.data as ekd
      >>> ds = ekd.from_source("fdb", request, read_all=True)

      # ds is empty at this point, but calling any method on it will
      # consume the whole stream
      >>> len(ds)
      3

      # now ds stores all the messages in memory

  Further examples:

      - :ref:`/examples/fdb.ipynb`
      - :ref:`/examples/grib_fdb_write.ipynb`


.. _data-sources-mars:

mars
--------------

.. py:function:: from_source("mars", *args, prompt=True, log="default", **kwargs)
  :noindex:

  The ``mars`` source will retrieve data from the ECMWF MARS (Meteorological Archival and Retrieval System) archive. In addition
  to data retrieval, the request specified as ``*args`` and/or ``**kwargs`` also has GRIB post-processing options such as ``grid`` and ``area`` for regridding and
  sub-area extraction, respectively.

  To figure out which data you need, or discover relevant data available in MARS, see the publicly accessible `MARS catalog`_ (or this `access restricted catalog <https://apps.ecmwf.int/mars-catalogue/>`_).

  If the ``use-standalone-mars-client-when-available`` :ref:`config option<config>` is True and the MARS client is installed (e.g. at ECMWF) the MARS access is direct. In this case the MARS client command can be specified via the ``MARS_CLIENT_EXECUTABLE`` environment variable. When it is not set the ``"/usr/local/bin/mars"`` path will be used.

  If the standalone MARS client is not available or not enabled the `web API`_ will be used. In order to use the `web API`_ you will need to register and retrieve an access token. For a more extensive documentation about MARS, please refer to the `MARS user documentation`_.

  :param tuple *args: positional arguments specifying the request as a dict
  :param bool prompt: if ``True``, it can offer a prompt to specify the credentials for `web API`_ and write them into the default RC file ``~/.ecmwfapirc``. The prompt only appears when:

    - no `web API`_ RC file exists at the default location ``~/.ecmwfapirc``
    - no `web API`_ RC file exists at the location specified via the ``ECMWF_API_RC_FILE`` environment variable
    - no credentials specified via the ``ECMWF_API_URL`` and ``ECMWF_API_KEY``  environment variables
  :param log: control the logging of the retrieval. The behaviour depends on the underlying MARS client used:

    - `web API`_ based access:

      - "default": the built-in logging of `web API`_ is used (the log is written to stdout)
      - None: turn off logging
      - callable: the log is written to the specified callable. The callable should accept a single argument, a string with the log message.

      .. code-block:: python

          import earthkit.data as ekd


          def my_logging_function(msg):
              print("message=", msg)


          request = {...}
          ds = ekd.from_source("mars", request, log=my_logging_function)

    - direct MARS access:

      - "default": log is written to stdout
      - None: turn off logging
      - dict specifying the "stdout" or/and the "stderr" kwargs for Pythons's ``subrocess.run()`` method

  :type log: str, None, callable, dict
  :param dict **kwargs: other keyword arguments specifying the request

  The following example retrieves analysis GRIB data for a subarea for 2 surface parameters:

  .. code-block:: python

      import earthkit.data as ekd

      ds = ekd.from_source(
          "mars",
          {
              "param": ["2t", "msl"],
              "levtype": "sfc",
              "area": [50, -50, 20, 50],
              "grid": [2, 2],
              "date": "2023-05-10",
          },
      )

  Data downloaded from MARS is stored in the :ref:`cache <caching>`.

  Further examples:

      - :ref:`/examples/mars.ipynb`


.. _data-sources-opendap:

opendap
--------

.. py:function:: from_source("opendap", url)
  :noindex:

  The ``opendap`` source accesses NetCDF data from `OPeNDAP <https://en.wikipedia.org/wiki/OPeNDAP>`_ services. OPenDAP is an acronym for "Open-source Project for a Network Data Access Protocol".

  :param str url: the url of the remote NetCDF file

  Examples:

      - :ref:`/examples/netcdf_opendap.ipynb`


.. _data-sources-polytope:

polytope
--------

.. py:function:: from_source("polytope", collection, *args, address=None, user_email=None, user_key=None, stream=True, read_all=False, **kwargs)
  :noindex:

  The ``polytope`` source accesses the `Polytope web services <https://polytope.readthedocs.io/en/latest/>`_ , using the polytope-client_ package.

  :param str collection: the name of the polytope collection
  :param tuple *args: specify the request as a dict
  :param str address: specify the address of the polytope service
  :param str user_email: specify the user email credential. Must be used together with ``user_key``. This is an alternative to using the ``POLYTOPE_USER_EMAIL`` environment variable. *New in version 0.7.0*
  :param str user_key: specify the user key credential. Must be used together with ``user_email``. This is an alternative to using the ``POLYTOPE_USER_KEY`` environment variable. *New in version 0.7.0*
  :param bool stream: if ``True``, the data is read as a :ref:`stream <streams>`. Otherwise it is retrieved into a file and stored in the :ref:`cache <caching>`. Stream-based access only works for :ref:`grib` and CoverageJson data. See details about streams :ref:`here <streams>`.
  :param bool read_all: if ``True``, all the data is read into memory from a :ref:`stream <streams>`. Used when ``stream=True``. *New in version 0.8.0*
  :param dict **kwargs: other keyword arguments, these can include options passed to the polytope-client_


  The following example retrieves GRIB data from the "ecmwf-mars" polytope collection:

  .. code-block:: python

      import earthkit.data as ekd

      request = {
          "stream": "oper",
          "levtype": "pl",
          "levellist": "1",
          "param": "130.128",
          "step": "0/12",
          "time": "00:00:00",
          "date": "20200915",
          "type": "fc",
          "class": "rd",
          "expver": "hsvs",
          "domain": "g",
      }

      ds = ekd.from_source("polytope", "ecmwf-mars", request, stream=False)

  Data downloaded from the polytope service is stored in the the :ref:`cache <caching>`. However,
  please note that, in the current version, each call to  :func:`from_source` will download the data again.

  To access data from polytope, you will need to register and retrieve an access token.

  Further examples:

      - :ref:`/examples/polytope.ipynb`
      - :ref:`/examples/polytope_feature.ipynb`
      - :ref:`/examples/polytope_time_series.ipynb`
      - :ref:`/examples/polytope_polygon_coverage.ipynb`
      - :ref:`/examples/polytope_vertical_profile.ipynb`

.. _data-sources-s3:

s3
---

.. py:function:: from_source("s3", *args, anon=True, aws_access_key=None, aws_secret_access_key=None, aws_token=None, stream=False, read_all=False)
  :noindex:

  *New in version 0.11.0*

  The ``s3`` source provides access to `Amazon S3 buckets <https://aws.amazon.com/s3/>`_.

  :param tuple *args: positional arguments specifying the request(s). Each request is represented by a dict. See detailed description below. A sequence of dicts can also be used to specify multiple requests.
  :param bool anon: if ``True`` use anonymous access, this will only work for public buckets. If ``False``, use the ``aws_access_key``, ``aws_secret_access_key`` and ``aws_token`` credentials. These can also be specified as part of the request (request values override the kwargs). If no credentials provided use :xref:`botocore` to load the `aws credentials`_ from:

    - `environment variables <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables>`_
    - `a configuration file <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-a-configuration-file>`_. Note that this does not include :xref:`s3cmd` configuration files (e.g. ".s3cfg").
  :param str aws_access_key: the AWS access key. Can be overridden in a request. Used when ``anon=False``.
  :param str aws_secret_access_key: the AWS secret access key. Can be overridden in a request. Used when ``anon=False``.
  :param str aws_token: the AWS token only used for AWS Security Token Service (AWS STS) temporary credentials. Can be overridden in a request. Used when ``anon=False``.
  :param bool stream: if ``True``, the data is read as a :ref:`stream <streams>`. Otherwise it is retrieved into a file and stored in the :ref:`cache <caching>`. Stream-based access only works for :ref:`grib` and CoverageJson data. See details about streams :ref:`here <streams>`.
  :param bool read_all: if ``True``, all the data is read into memory from a :ref:`stream <streams>`. Used when ``stream=True``.

  A **request** is a dictionary describing a single or multiple objects in a given bucket. It has the following format:

      .. code-block::

          {
              "endpoint": endpoint,  # optional
              "region": region,  # optional
              "bucket": bucket,
              "objects": objects,
              "aws_access_key": aws_access_key,  # optional
              "aws_secret_access_key": aws_secret_access_key,  # optional
              "aws_token": aws_token,  # optional
          }

  where:

        - "endpoint": specifies the S3 endpoint (optional). Defaults to ``"s3.amazonaws.com"``
        - "region": specifies the AWS region (optional). Defaults to ``"eu-west-2"``
        - "bucket": specifies the bucket name
        - "objects": specifies the object in the bucket. A list/tuple of objects can be provided.
        - "aws_access_key": the AWS access key (optional). It overrides ``aws_access_key``. Only used when ``anon=False``.
        - "aws_secret_access_key": the AWS secret access key (optional). It overrides ``aws_secret_access_key``. Only used when ``anon=False``.
        - "aws_token": the AWS token (optional). It overrides ``aws_token``. Only used when ``anon=False``.


  An object can be:

    - the name of the object as a str
    - a dict in the following format:

      .. code-block::

          {"object": name, "parts": parts}

      where the optional "parts" can specify the :ref:`parts <parts>` (byte ranges) to read.


  The following examples retrieve :ref:`grib` data from a publicly available bucket on the European Weather Cloud (EWC).

  .. code-block:: python

    >>> import earthkit.data as ekd
    >>> req = {
    ...     "endpoint": "object-store.os-api.cci1.ecmwf.int",
    ...     "bucket": "earthkit-test-data-public",
    ...     "objects": "test6.grib",
    ... }
    >>> ds = ekd.from_source("s3", req, anon=True)
    >>> ds.ls()
      centre shortName    typeOfLevel  level  dataDate  dataTime stepRange dataType  number    gridType
    0   ecmf         t  isobaricInhPa   1000  20180801      1200         0       an       0  regular_ll
    1   ecmf         u  isobaricInhPa   1000  20180801      1200         0       an       0  regular_ll
    2   ecmf         v  isobaricInhPa   1000  20180801      1200         0       an       0  regular_ll
    3   ecmf         t  isobaricInhPa    850  20180801      1200         0       an       0  regular_ll
    4   ecmf         u  isobaricInhPa    850  20180801      1200         0       an       0  regular_ll
    5   ecmf         v  isobaricInhPa    850  20180801      1200         0       an       0  regular_ll


  .. code-block:: python

    >>> req = {
    ...     "endpoint": "object-store.os-api.cci1.ecmwf.int",
    ...     "bucket": "earthkit-test-data-public",
    ...     "objects": [
    ...         {"object": "test6.grib", "parts": (0, 240)},
    ...         {"object": "tuv_pl.grib", "parts": (2400, 240)},
    ...     ],
    ... }
    >>>
    >>> ds = ekd.from_source("s3", req, anon=True)
    >>> ds.ls()
      centre shortName    typeOfLevel  level  dataDate  dataTime stepRange dataType  number    gridType
    0   ecmf         t  isobaricInhPa   1000  20180801      1200         0       an       0  regular_ll
    1   ecmf         u  isobaricInhPa    500  20180801      1200         0       an       0  regular_ll


  Further examples:

      - :ref:`/examples/s3.ipynb`


.. _data-sources-wekeo:

wekeo
-----

.. py:function:: from_source("wekeo", dataset, *args, prompt=True, **kwargs)
  :noindex:

  `WEkEO`_ is the Copernicus DIAS reference service for environmental data and virtual processing environments. The ``wekeo`` source provides access to `WEkEO`_ using the WEkEO grammar. The retrieval is based on the hda_ Python API.

  :param str dataset: the name of the WEkEO dataset
  :param tuple *args: specify the request as a dict
  :param bool prompt: if ``True``, it can offer a prompt to specify the credentials for hda_ and write them into the default RC file ``~/.hdarc``. The prompt only appears when:

    - no hda_ RC file exists at the default location ``~/.hdarc``
    - no hda_ RC file exists at the location specified via the ``HDA_RC`` environment variable
    - no credentials specified via the ``HDA_USER`` and ``HDA_PASSWORD`` environment variables
  :param dict **kwargs: other keyword arguments specifying the request

  The following example retrieves Normalized Difference Vegetation Index data derived from EO satellite imagery in NetCDF format:

  .. code-block:: python

      import earthkit.data as ekd

      ds = ekd.from_source(
          "wekeo",
          "EO:CLMS:DAT:CLMS_GLOBAL_BA_300M_V3_MONTHLY_NETCDF",
          request={
              "dataset_id": "EO:CLMS:DAT:CLMS_GLOBAL_BA_300M_V3_MONTHLY_NETCDF",
              "startdate": "2019-01-01T00:00:00.000Z",
              "enddate": "2019-01-01T23:59:59.999Z",
          },
      )


  Data downloaded from WEkEO is stored in the the :ref:`cache <caching>`.

  To access data from WEkEO, you will need to register and set up the Harmonized Data Access (HDA) API client. The process is described `here <https://help.wekeo.eu/en/articles/6751608-what-is-the-hda-api-python-client-and-how-to-use-it>`_.

  Further examples:

      - :ref:`/examples/wekeo.ipynb`


.. _data-sources-wekeocds:

wekeocds
--------

.. py:function:: from_source("wekeocds", dataset, *args, prompt=True, **kwargs)
  :noindex:

  `WEkEO`_ is the Copernicus DIAS reference service for environmental data and virtual processing environments. The ``wekeocds`` source provides access to `Copernicus Climate Data Store`_ (CDS) datasets served on `WEkEO`_ using the `cdsapi`_ grammar. The retrieval is based on the hda_ Python API.

  :param str dataset: the name of the WEkEO dataset
  :param tuple *args: specify the request as a dict
  :param bool prompt: if ``True``, it can offer a prompt to specify the credentials for hda_ and write them into the default RC file ``~/.hdarc``. The prompt only appears when:

    - no hda_ RC file exists at the default location ``~/.hdarc``
    - no hda_ RC file exists at the location specified via the ``HDA_RC`` environment variable
    - no credentials specified via the ``HDA_USER`` and ``HDA_PASSWORD`` environment variables
  :param dict **kwargs: other keyword arguments specifying the request

  The following example retrieves ERA5 surface data for multiple days in GRIB format:

  .. code-block:: python

      import earthkit.data as ekd

      ds = ekd.from_source(
          "wekeocds",
          "EO:ECMWF:DAT:REANALYSIS_ERA5_SINGLE_LEVELS_MONTHLY_MEANS_MONTHLY_MEANS",
          variable=["2m_temperature", "mean_sea_level_pressure"],
          product_type=["monthly_averaged_reanalysis_by_hour_of_day"],
          year=["2012"],
          month=["12"],
          time=["11:00"],
          data_format="grib",
          download_format="zip",
      )

  Data downloaded from WEkEO is stored in the the :ref:`cache <caching>`.

  To access data from WEkEO, you will need to register and set up the Harmonized Data Access (HDA) API client. The process is described `here <https://help.wekeo.eu/en/articles/6751608-what-is-the-hda-api-python-client-and-how-to-use-it>`_.

  Further examples:

      - :ref:`/examples/wekeo.ipynb`



.. _data-sources-zarr:

zarr
--------

.. py:function:: from_source("zarr", path)
  :noindex:

  *New in version 0.15.0*

  The ``zarr`` source accesses data from a `Zarr <https://zarr.readthedocs.io/en/stable/>`_ store. Internally the data is loaded via the :py:meth:`xarray.open_zarr` method,  so only Zarr data supported by Xarray can be accessed. Requires ``zarr >= 3`` version.

  :param str path: path or URL to the Zarr store




.. _MARS catalog: https://apps.ecmwf.int/archive-catalogue/
.. _MARS user documentation: https://confluence.ecmwf.int/display/UDOC/MARS+user+documentation
.. _web API: https://www.ecmwf.int/en/forecasts/access-forecasts/ecmwf-web-api

.. _Copernicus Climate Data Store: https://cds.climate.copernicus.eu/
.. _Copernicus Atmosphere Data Store: https://ads.atmosphere.copernicus.eu/
.. _cdsapi: https://pypi.org/project/cdsapi/
.. _CDS_knowledge base: https://confluence.ecmwf.int/pages/viewpage.action?pageId=151530614
.. _ADS_knowledge base: https://confluence.ecmwf.int/pages/viewpage.action?pageId=151530675

.. _ECMWF open data: https://www.ecmwf.int/en/forecasts/datasets/open-data

.. _WEkEO: https://www.wekeo.eu/
.. _hda: https://pypi.org/project/hda

.. _polytope-client: https://pypi.org/project/polytope-client

.. _aws credentials: http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials
