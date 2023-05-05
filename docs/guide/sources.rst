.. _data-sources:

Data sources
============

A Data Source is an object created using ``earthkit.data.from_source(name, *args, **kwargs)``
with the appropriate name and arguments, which provides data and additional functionalities.

    .. code-block:: python

        import earthkit.data

        source = earthkit.data.from_source(name, "argument1", "argument2", ...)

    - The **name** is a string that uniquely identifies the source type.

    - The ``*args`` are used to specify the data location to access the data.
      They can include additional parameters to access the data.

    - The ``**kwargs`` provide **additional functionalities** including caching, filtering, sorting and indexing.


**earthkit-data** has the following built-in sources:.

.. list-table:: Data sources
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
   * - :ref:`data-sources-stream`
     - read data from a stream
   * - :ref:`data-sources-memory`
     - read data from a memory buffer

The data source object provides methods to access and use its data, such as
``to_xarray()`` or ``to_pandas()`` or other. Depending on the data, some of
these methods may not be available.

    .. code-block:: python

        source.to_xarray()  # for gridded data
        source.to_pandas()  # for non-gridded data
        source.to_numpy()


----------------------------------


.. _data-sources-file:

file
----

.. py:function:: from_source("file", path, expand_user=True, expand_vars=False, unix_glob=True, recursive_glob=True)
  :noindex:

  The simplest data source is the *file* source that can access a local file/list of files.

  :param path: input path(s)
  :type path: str, list
  :param bool expand_user: replaces the leading ~ or ~user in ``path`` by that user's home directory. See ``os.path.expanduser``
  :param bool expand_vars:  expands shell environment variables in ``path``. See ``os.path.expandpath``
  :param bool unix_glob: allows UNIX globbing in ``path``
  :param bool recursive_glob: allows recursive scanning of directories. Only used when ``uxix_glob`` is True

  *earthkit-data* will inspect the content of the files to check for any of the
  supported data formats listed below:

  - Fields:
      - NetCDF
      - GRIB

  - Observations:
      - CSV (comma-separated values)
      - BUFR


  When the input is an archive format such as ``.zip``, ``.tar``, ``.tar.gz``, etc,
  *earthkit-data* will attempt to open it and extract any usable files, which are then stored in the :ref:`cache <caching>`.

  The ``path`` can be used in a flexible way:

    .. code:: python

        import earthkit.data

        # UNIX globbing is allowed by default
        data = earthkit.data.from_source("file", "path/to/t_*.grib")

        # list of files can be specified
        data = earthkit.data.from_source("file", ["path/to/f1.grib", "path/to/f2.grib"])

        # a path can be a directory, in this case it is recursively scanned for supported files
        data = earthkit.data.from_source("file", "path/to/dir")


  See the following notebook examples for further details:

    - :ref:`/examples/grib_multi.ipynb`

.. _data-sources-file-pattern:

file-pattern
--------------

.. py:function:: from_source("file-pattern", pattern, *args, **kwargs)

  The *file-pattern* data source will build paths from the pattern specified,
  using the other arguments to fill the pattern. Each argument can be a list
  to iterate and create the cartesian product of all lists.
  Then each file is read in the same ways as with :ref:`file source <data-sources-file>`.

  .. code-block:: python

      import datetime
      import earthkit.data

      data = earthkit.data.from_source(
          "file-pattern",
          "path/to/data-{my_date:date(%Y-%m-%d)}-{run_time}-{param}.grib",
          {
              "my_date": datetime.datetime(2020, 5, 2),
              "run_time": [12, 18],
              "param": ["t2", "msl"],
          },
      )


  The code above will read the following files:

  #. \path/to/data-2020-05-02-12-t2.grib
  #. \path/to/data-2020-05-02-12-msl.grib
  #. \path/to/data-2020-05-02-18-t2.grib
  #. \path/to/data-2020-05-02-18-msl.grib


.. _data-sources-url:

url
---

.. py:function:: from_source("url", url, unpack=True)

  The *url* data source will download the data from the address specified and store it in the :ref:`cache <caching>`. The supported data formats are the same as for the :ref:`file <data-sources-file>` data source above.

  :param url: the URL to download
  :type url: str
  :param bool unpack: for archive formats such as ``.zip``, ``.tar``, ``.tar.gz``, etc, *earthkit-data* will attempt to open it and extract any usable file. To keep the downloaded file as is use ``unpack=False``

  .. code-block:: python

      import earthkit.data

      data = earthkit.data.from_source("url", "https://www.example.com/data.csv")


.. _data-sources-url-pattern:

url-pattern
-----------

.. py:function:: from_source("url-pattern", url, unpack=True)

  The *url-pattern* data source will build urls from the pattern specified,
  using the other arguments to fill the pattern. Each argument can be a list
  to iterate and create the cartesian product of all lists.
  Then each url is downloaded and stored in the :ref:`cache <caching>`. The
  supported download the data from the address data formats are the same as
  for the *file* and *url* data sources above.

  .. code-block:: python

      import climetlab as cml

      data = cml.load_source(
          "url-pattern",
          "https://www.example.com/data-{foo}-{bar}-{qux}.csv",
          foo=[1, 2, 3],
          bar=["a", "b"],
          qux="unique",
      )

  The code above will download and process the data from the six following urls:

  #. \https://www.example.com/data-1-a-unique.csv
  #. \https://www.example.com/data-2-a-unique.csv
  #. \https://www.example.com/data-3-a-unique.csv
  #. \https://www.example.com/data-1-b-unique.csv
  #. \https://www.example.com/data-2-b-unique.csv
  #. \https://www.example.com/data-3-b-unique.csv

  If the urls are pointing to archive format, the data will be unpacked by
  ``url-pattern`` according to the **unpack** argument, similarly to what
  the source ``url`` does (see above the :ref:`data-sources-url` source).


  Once the data have been properly downloaded [and unpacked] and cached. It can
  can be accessed using ``to_xarray()`` or ``to_pandas()``.

  To provide a unique xarray.Dataset (or pandas.DataFrame), the different
  datasets are merged.
  The default merger strategy for field data is to use ``xarray.open_mfdataset``
  from `xarray`. This can be changed by providing a custom merger to the
  ``url-pattern`` source. See :ref:`merging sources <custom-merge>`

.. _data-sources-stream:

stream
--------------

.. py:function:: from_source("stream", stream, group_by=1)

  The *stream* source will read data from a stream, which can be an FDB stream, a standard Python IO stream or any object implementing the necessary stream methods. At the moment tt only works for GRIB data.

  :param stream: the stream
  :param bool group_by: defines how many GRIB messages are consumed from the stream and kept in memory at a time. ``groub_by=0`` means all the messages will be loaded and stored in memory.

  When ``groub_by`` is not zero ``from_source`` gives us a stream iterator object. During the iteration temporary objects are created for each message then get deleted when going out of scope.

  Let us imagine we have 4 GRIB messages available in a stream. By default (``group_by=1``) we will consume one message at a time:

  .. code-block:: python

      import earthkit.data

      data = earthkit.data.from_source("stream", stream)
      for f in data:
          # f is a GribField
          print(f.metadata("param"))

  Output: ::

      GribField(u,1000,20180801,1200,0,0)
      GribField(v,1000,20180801,1200,0,0)
      GribField(u,500,20180801,1200,0,0)
      GribField(v,500,20180801,1200,0,0)

  We can use ``group_by=2`` to read 2 messages at a time:

  .. code-block:: python

      >>> import earthkit.data
      >>> data = earthkit.data.from_source("stream", stream, group_by=2)

      # f is a FieldList containing 2 GribFields
      >>> for f in data:
      ...     print(f.metadata("param"))
      ...
      ['u', 'v']
      ['u', 'v']

  With ``groub_by=0`` the whole stream will be consumed resulting in a FieldList object storing all the messages in memory. **Use this option carefully!**

  .. code-block:: python

      >>> import earthkit.data
      >>> data = earthkit.data.from_source("stream", stream, group_by=0)

      # data is empty at this point, but calling any method on it will
      # consume the whole stream
      >>> len(data)
      4

      # now data stores all the messages in memory

  See the following notebook examples for further details:

    - :ref:`/examples/grib_from_stream.ipynb`
    - :ref:`/examples/grib_fdb_stream.ipynb`


.. _data-sources-memory:

memory
--------------

.. py:function:: from_source("memory", buffer)

  The *memory* source will read data from a memory buffer. Currently it only works for a ``buffer`` storing a single GRIB message.

  Please note that a buffer can always be read as a :ref:`stream source <data-sources-stream>` using ``io.BytesIO``.

  .. code-block:: python

      import io
      import earthkit.data

      # buffer stores GRIB messages
      stream = io.BytesIO(buffer)

      data = earthkit.data.from_source("stream", stream)
      for f in data:
          print(f.metadata("param"))
