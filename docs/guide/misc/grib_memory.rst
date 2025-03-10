.. _grib-memory:

GRIB field memory management
//////////////////////////////

:ref:`grib` is a message-based binary format, where each message is regarded as a field. For reading GRIB, earthkit-data relies on :xref:`eccodes`, which, when loading a message into memory, represents it as a ``GRIB handle``. In the low level API, the GRIB handle is the object that holds the data and metadata of a GRIB field, therefore it can use up a significant amount of memory.

Determining when a GRIB handle needs to be created and when it can be released is important for memory management. Earthkit-data provides several config options to control this behaviour depending on how we actually read the data.

Reading GRIB data as a stream iterator
========================================

We can read :ref:`grib` data as a :ref:`stream <streams>` iterator e.g. with the following code:

.. code-block:: python

    import earthkit.data as ekd

    url = "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test6.grib"
    ds = ekd.from_source("url", url, stream=True)
    for f in fields:
        print(f)

Here, field ``f`` is not attached to a fieldlist and only exists in the scope of the iteration (in the for loop). During its existence the field keeps the GRIB handle in memory and if used in the way shown above, only one field can exist at a time. Once the stream is consumed there is no way to access the data again (unless we read it with :func:`from_source` again).

Reading all GRIB data from a stream into memory
===============================================

We can load :ref:`grib` data fully into memory when we read it as a :ref:`stream <streams>` with the ``read_all=True`` option in :func:`from_source`.

.. code-block:: python

    import earthkit.data as ekd

    url = "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test6.grib"
    ds = ekd.from_source("url", url, stream=True, read_all=True)

With this, the entire ``ds`` fieldlist, including all the fields and the related GRIB handles, are stored in memory.

Reading data from disk and managing its memory
==============================================

When reading :ref:`grib` data from disk as a :ref:`file source <data-sources-file>`, it is represented as a fieldlist and loaded lazily. After the (fast) initial scan for field offsets and lengths, no actual fields are created and no data is read into memory. When we start using the fieldlist, e.g. by iterating over the fields, accessing data or metadata etc., the fields will be created **on demand** and the related GRIB handles will be loaded from disk **when needed**. Whether this data or part of it stays in memory depends on the following :ref:`config <config>`:

- :ref:`grib-field-policy <grib-field-policy>`
- :ref:`grib-handle-policy <grib-handle-policy>`
- :ref:`grib-handle-cache-size <grib-handle-cache-size>`

.. _grib-field-policy:

grib-field-policy
++++++++++++++++++++++++++++

Controls whether fields are kept in memory. The default is ``"persistent"``. The possible values are:

- ``"persistent"``: fields are kept in memory until the fieldlist is deleted
- ``"temporary"``: fields are deleted when they go out of scope and recreated on demand

The actual memory used by a field depends on whether it owns the GRIB handle of the related GRIB message. This is controlled by the :ref:`grib-handle-policy <grib-handle-policy>` config option.

A field can also cache its metadata access for performance, thus increasing memory usage. This is controlled by the :ref:`use-grib-metadata-cache <use-grib-metadata-cache>` config option.

.. _grib-handle-policy:

grib-handle-policy
++++++++++++++++++++++++++++

Controls whether GRIB handles are kept in memory. The default is ``"cache"``. The possible values are:

- ``"cache"``: a separate in-memory LRU cache is created for the GRIB handles in the fieldlist. The maximum number of GRIB handles kept in this cache is controlled by :ref:`grib-handle-cache-size <grib-handle-cache-size>`. In this mode, field objects are lightweight and only store the GRIB handle cache index, and can only access the GRIB handles via the cache.
- ``"persistent"``: once a GRIB handle is created, a field keeps it in memory until the field is deleted
- ``"temporary"``: for each call to data and metadata access on a field, a new GRIB handle is created and released once the access has finished.

.. _grib-handle-cache-size:

grib-handle-cache-size
++++++++++++++++++++++++++++

When :ref:`grib-handle-policy <grib-handle-policy>` is ``"cache"``, the config option ``grib-handle-cache-size`` (default is ``1``) specifies the maximum number of GRIB handles kept in an in-memory cache per fieldlist. This is an LRU cache, so when it is full, the least recently used GRIB handle is removed and a new GRIB message is loaded from disk and added to the cache.

Overriding the configuration
++++++++++++++++++++++++++++

In addition to changing the :ref:`config`, it is possible to override the parameters discussed above when loading a given fieldlist by passing them as keyword arguments to :func:`from_source`. The parameter names are the same but the dashes are replaced by underscores. When a parameter is not specified in :func:`from_source` or is set to None, its value is taken from the actual :ref:`config`. E.g.:

.. code-block:: python

    import earthkit.data as ekd

    ds = ekd.from_source(
        "file",
        "test6.grib",
        grib_field_policy="persistent",
        grib_handle_policy="temporary",
        grib_handle_cache_size=0,
    )


Reading data from disk as a stream
++++++++++++++++++++++++++++++++++

Whilst the usual way of reading GRIB data from disk loads fields lazily (i.e. only when they are actually used), it is also possible to read all
fields up-front and keep them in memory by reading it as a :ref:`stream source <data-sources-stream>` with the ``read_all=True`` option.

.. code-block:: python

    import earthkit.data as ekd

    f = open("test6.grib", "rb")
    ds = ekd.from_source("stream", f, read_all=True)

.. warning::

    Use this option carefully since your data might not fit into memory.



.. note::
   The default config options are chosen to keep the memory usage low and the performance high. However, depending on the use case, the configuration can be adjusted to optimize the memory
   usage and performance.
