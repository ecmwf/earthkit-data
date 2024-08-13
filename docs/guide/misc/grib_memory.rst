.. _grib-memory:

GRIB field memory management
//////////////////////////////

:ref:`grib` is a message-based binary format, where each message is regarded as a field. For reading GRIB earthkit-data relies on :xref:`eccodes`, which when loading a message into memory representing it as a ``GRIB handle``. In the low level API the GRIB handle is the object that stores the data and metadata of a GRIB field, therefore it can use up a significant amount of memory.

Determining when a GRIB handle needs to be created and when it can be released is important for memory management. Earthkit-data provides several settings to control this behaviour depending on how we actually read the data.

Reading GRIB data as a stream iterator
========================================

We can read :ref:`grib` data as a :ref:`stream <streams>` iterator e.g. with the following code:

.. code-block:: python

    import earthkit.data

    url = "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test6.grib"
    ds = earthkit.data.from_source("url", url, stream=True)
    for f in fields:
        print(f)

Here field ``f`` is not attached to a fieldlist and only exists in the scope of the iteration (in the for loop). During its existence the field keeps the GRIB handle in memory and if used in the way shown above, only one field can exist at a time. Once the stream is consumed there is no way to access the data again (unless we read it with :func:`from_source` again).

Reading all the GRIB data into memory
========================================

We can load :ref:`grib` data fully into memory when we read it as a :ref:`stream <streams>` with the ``read_all=True`` option in :func:`from_source`.

.. code-block:: python

    import earthkit.data

    url = "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test6.grib"
    ds = earthkit.data.from_source("url", url, stream=True, read_all=True)

With this the entire ``ds`` fieldlist, including all the fields and the related GRIB handles, are stored in memory.

This technique also works for GRIB data on disk, we just need to read it as a :ref:`stream source <data-sources-stream>`.

.. code-block:: python

    import earthkit.data

    f = open("test6.grib", "rb")
    ds = earthkit.data.from_source("stream", f, read_all=True)

.. warning::

    Use this option carefully since your data might not fit into memory.

Reading data from disk and partially store it in memory
===========================================================

When reading :ref:`grib` data from disk as a :ref:`file source <data-sources-file>` it is represented as a fieldlist and loaded lazily. After the (fast) initial scan for field offsets and lengths, no actual fields are created and no data is read into memory. When we start using the fieldlist, e.g. by iterating over the fields, accessing data or metadtata etc., the fields will be created on demand and the related GRIB handles will be loaded from disk when needed. Whether this data or part of it stays in memory depends on the following :ref:`settings <settings>`:

- :ref:`store-grib-fields-in-memory <store-grib-fields-in-memory>`
- :ref:`grib-handle-cache-size <grib-handle-cache-size>`
- :ref:`use-grib-metadata-cache <use-grib-metadata-cache>`

.. _store-grib-fields-in-memory:

store-grib-fields-in-memory
++++++++++++++++++++++++++++

When ``store-grib-fields-in-memory`` is ``True`` (this is the default), once a field is created it will be stored in the fieldlist. Otherwise the field will be created on demand and deleted when it goes out of scope.

The actual memory used by a field depends on whether it stores the GRIB handle of the related GRIB message. This is controlled by the :ref:`grib-handle-cache-size <grib-handle-cache-size>` settings:

 - When ``grib-handle-cache-size > 0`` the field objects themselves are lightweight and only store the GRIB handle cache index, while the actual GRIB handles are stored in the cache, which is attached to the fieldlist.
 - When ``grib-handle-cache-size == 0`` the behaviour depends on ``store-grib-fields-in-memory``:

    - when ``store-grib-fields-in-memory`` is ``True`` the fields do not own their GRIB handle but for each call to data and metadata access, a new GRIB handle is created and released once the access has finished. This can be useful when the fields have to be kept in memory but the memory usage should be kept low.
    - when ``store-grib-fields-in-memory`` is ``False`` the fields are created on demand and will store their own GRIB handle in memory until they get deleted (when going out of scope).


.. _grib-handle-cache-size:

grib-handle-cache-size
++++++++++++++++++++++++++++

When ``grib-handle-cache-size`` is set to a positive value (default is 1) an in-memory GRIB handle cache is attached to the fieldlist. The cache size determines how many GRIB handles are stored in memory. This is an LRU cache so when it is full the least recently used GRIB handle is removed and a new GRIB message is loaded from disk and added to the cache.


.. _use-grib-metadata-cache:

use-grib-metadata-cache
+++++++++++++++++++++++++++++++++++

When ``use-grib-metadata-cache`` is ``True`` (this is the default) all the fields will cache their metadata access. This is an in memory-cache attached to the field and implemented for the low-level metadata accessor for individual keys. The metadata cache can be useful when the same metadata keys are accessed multiple times for the same field.
