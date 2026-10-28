.. _grib-index-object:

Using the GribIndex class
/////////////////////////

The :py:class:`~earthkit.data.readers.grib.index.GribIndex` class is the object behind the :ref:`GRIB metadata index <grib-index>`. It is a small wrapper around a `sqlite <https://www.sqlite.org>`_ database that stores the metadata of the messages of one or more GRIB files. ``to_fieldlist(index=...)`` uses it internally, so most users never need to create one themselves. Use the class directly when you want to prepare an index database in advance, check what a database contains, or read the stored metadata without building a fieldlist.

The class is not exported by ``earthkit.data``, it has to be imported from the module where it is defined:

.. code-block:: python

    from earthkit.data.readers.grib.index import GribIndex

All the examples below use placeholder file names ("data1.grib", "data2.grib", "data3.grib", "my_index.db"). See the :ref:`/tutorials/grib/grib_metadata_index.ipynb` notebook for a worked example of the index in use.

Methods at a glance
===================

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Method
      - Purpose
    * - :py:class:`GribIndex(path, overwrite=False) <earthkit.data.readers.grib.index.GribIndex>`
      - Open (or create) a database file. Nothing is scanned.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.open`
      - Open a database and make sure one or more GRIB files are indexed in it.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.from_file`
      - Index a single GRIB file. A thin wrapper around ``open()``.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.add_file`
      - Make sure a GRIB file is indexed in an open database.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.cache_db_path`
      - Get the path of the database of a GRIB file in the earthkit-data cache.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.find_in_cache`
      - Open the up-to-date database of a GRIB file from the cache, if there is one.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.close`
      - Close the database. The object can also be used in a ``with`` statement.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.count`
      - Number of messages in the database, or in one GRIB file.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.paths`
      - Paths of the GRIB files in the database.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.has_path`
      - Tell if a GRIB file is in the database.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.extra_keys`
      - Extra GRIB keys that were scanned for a file.
    * - :py:meth:`~earthkit.data.readers.grib.index.GribIndex.rows`
      - Iterate over the stored metadata of the messages of a file.

Creating an index
=================

Constructor
+++++++++++

``GribIndex(path, *, overwrite=False)`` opens the database file ``path``, and creates it if it does not exist. It does **not** scan any GRIB file, so a new database is empty. With ``overwrite=True`` an existing database file is removed first.

.. code-block:: python

    from earthkit.data.readers.grib.index import GribIndex

    db = GribIndex("my_index.db")
    db.count()  # 0
    db.close()

    # start again from an empty database
    db = GribIndex("my_index.db", overwrite=True)
    db.close()

If the file exists but was created with another version of the database schema, a ``ValueError`` is raised and the file has to be removed to be recreated.

The constructor is the low-level way to get a database. :py:meth:`~earthkit.data.readers.grib.index.GribIndex.open` is usually more convenient because it also indexes the GRIB files.

open()
++++++

``GribIndex.open(path, db_path=None, extra_keys=None)`` opens a database and makes sure the GRIB files are indexed in it. ``path`` is a single file or a list of files. The returned object has to be closed by the caller (see :ref:`below <grib-index-object-close>`).

- ``db_path`` is the database file. It is created when needed and can hold any number of GRIB files.
- when ``db_path`` is ``None`` the database is stored in the earthkit-data :ref:`cache <caching>` and holds a single GRIB file (see :ref:`below <grib-index-object-cache>`). Giving more than one file without ``db_path`` raises a ``ValueError``.
- ``extra_keys`` is a key or a list of GRIB keys to store in addition to the default set. They are stored as ``metadata.<key>`` (see :ref:`here <grib-index>`).

New files are scanned (a progress bar is shown), files that are already in the database and unchanged are reused, and changed files are scanned again. See :py:meth:`~earthkit.data.readers.grib.index.GribIndex.add_file` for the details.

.. code-block:: python

    from earthkit.data.readers.grib.index import GribIndex

    # one database file for several GRIB files
    db = GribIndex.open(["data1.grib", "data2.grib"], db_path="my_index.db")
    db.count()  # 12
    db.close()

    # with extra keys
    db = GribIndex.open("data1.grib", db_path="my_index_extra.db", extra_keys=["bitsPerValue"])
    db.extra_keys("data1.grib")  # ['bitsPerValue']
    db.close()

    # without db_path only a single file is accepted
    GribIndex.open(["data1.grib", "data2.grib"])  # ValueError

from_file()
+++++++++++

``GribIndex.from_file(path, db_path=None, extra_keys=None)`` indexes a single GRIB file. It is a thin wrapper around ``open()`` with the same arguments.

.. code-block:: python

    from earthkit.data.readers.grib.index import GribIndex

    db = GribIndex.from_file("data1.grib", db_path="my_index_one.db")
    db.count()  # 6
    db.close()

add_file()
++++++++++

``db.add_file(path, extra_keys=None)`` makes sure one GRIB file is indexed in an open database. It returns ``True`` if the file was scanned and ``False`` if the existing entry was reused:

- a file that is not in the database is scanned and added
- a file that is in the database with the same size and modification time, and was already scanned for all the ``extra_keys``, is reused. Nothing is scanned or written
- otherwise (the file has changed, or some of the ``extra_keys`` were not scanned for it) the old entry of the file is replaced by a new scan. The keys scanned before are kept

A file is scanned and stored in one transaction, so if the scan fails the database stays as it was.

.. code-block:: python

    from earthkit.data.readers.grib.index import GribIndex

    db = GribIndex("my_index.db", overwrite=True)
    db.add_file("data1.grib")  # True, the file is scanned
    db.add_file("data1.grib")  # False, the file is reused
    db.add_file("data1.grib", extra_keys=["bitsPerValue"])  # True, scanned again with the new key
    db.add_file("data1.grib", extra_keys=["bitsPerValue"])  # False
    db.close()

Paths are always made absolute, so a relative and an absolute path to the same file are equivalent. Symbolic links are not resolved, so a link and its target count as different files.

.. _grib-index-object-cache:

Databases in the cache
======================

Instead of a database file of your own, a GRIB file can have its database in the earthkit-data :ref:`cache <caching>`. This is what ``to_fieldlist(index=True)`` does. It needs the :ref:`cache-policy <cache_policies>` to be "user" or "temporary". With the default policy ("off") the two methods below raise a ``ValueError``, and so do ``open()`` and ``from_file()`` when ``db_path`` is ``None``.

The name of the database in the cache is computed from the path of the GRIB file, its timestamps and size, the extra keys and the version of the database schema. So a changed file, or a different set of extra keys, has a different database.

cache_db_path()
+++++++++++++++

``GribIndex.cache_db_path(path, extra_keys=None, create=False)`` returns the path of the database of a GRIB file in the cache. The GRIB file must exist. With ``create=False`` (the default) nothing is created, so the database may not exist yet. With ``create=True`` an empty database file is created in the cache if it does not exist.

.. code-block:: python

    import os

    import earthkit.data as ekd
    from earthkit.data.readers.grib.index import GribIndex

    ekd.config.set("cache-policy", "user")

    db_path = GribIndex.cache_db_path("data3.grib")
    os.path.exists(db_path)  # False, it has not been created

    # a different set of extra keys gives a different database
    GribIndex.cache_db_path("data3.grib", extra_keys=["bitsPerValue"]) != db_path  # True

find_in_cache()
+++++++++++++++

``GribIndex.find_in_cache(path, extra_keys=None)`` returns the open database of a GRIB file from the cache, or ``None`` if there is no database for the file, or it is not up to date (the file has changed, or not all ``extra_keys`` were scanned). It has no side effects: nothing is created, written or scanned. The caller has to close the returned object.

.. code-block:: python

    import earthkit.data as ekd
    from earthkit.data.readers.grib.index import GribIndex

    ekd.config.set("cache-policy", "user")

    GribIndex.find_in_cache("data3.grib")  # None, not indexed yet

    # index the file in the cache (db_path is not given)
    with GribIndex.open("data3.grib") as db:
        db.count()  # 6

    # now it is found
    with GribIndex.find_in_cache("data3.grib") as db:
        db.count()  # 6

    # but not with an extra key that was not scanned
    GribIndex.find_in_cache("data3.grib", extra_keys="bitsPerValue")  # None

.. _grib-index-object-close:

Closing the database
====================

A ``GribIndex`` holds an open sqlite connection. Call ``close()`` when you are done with it. It is safe to call it more than once. The best way is to use the object as a context manager, which closes the database at the end of the ``with`` block, even if an error occurs.

.. code-block:: python

    from earthkit.data.readers.grib.index import GribIndex

    with GribIndex.open("data1.grib", db_path="my_index.db") as db:
        db.count()  # 6

    # explicit close
    db = GribIndex.open("data1.grib", db_path="my_index.db")
    try:
        db.count()  # 6
    finally:
        db.close()

Reading an index
================

The following methods read the content of an open database. Paths can be given as ``str`` or ``os.PathLike`` and are made absolute, so a relative path works as long as it points to the same file. Symbolic links are not resolved, so a link and its target count as different files.

.. code-block:: python

    from earthkit.data.readers.grib.index import GribIndex

    db = GribIndex.open(["data1.grib", "data2.grib"], db_path="my_index_two.db")

count()
+++++++

``db.count(path=None)`` returns the number of messages in the whole database, or in one GRIB file if ``path`` is given. A file that is not in the database has 0 messages.

.. code-block:: python

    db.count()  # 12
    db.count("data1.grib")  # 6
    db.count("data3.grib")  # 0, not in the database

paths()
+++++++

``db.paths()`` returns the list of the paths of the GRIB files in the database, in the order they were added.

.. code-block:: python

    db.paths()  # ['/path/to/data1.grib', '/path/to/data2.grib']

has_path()
++++++++++

``db.has_path(path)`` returns ``True`` if the GRIB file is in the database.

.. code-block:: python

    db.has_path("data1.grib")  # True
    db.has_path("data3.grib")  # False

extra_keys()
++++++++++++

``db.extra_keys(path)`` returns the list of the extra GRIB keys (without the ``metadata.`` prefix) that were scanned for a file, in addition to the default set. The list is empty when no extra key was requested. A ``ValueError`` is raised if the file is not in the database.

.. code-block:: python

    db.extra_keys("data1.grib")  # []
    db.extra_keys("data3.grib")  # ValueError

rows()
++++++

``db.rows(path)`` returns an iterator over the stored metadata of the messages of a GRIB file, ordered by their offset in the file. Each message is a ``dict`` with:

- ``_offset`` and ``_length``: the position and the size of the message in the file, in bytes
- the keys of the fieldlist components, e.g. ``parameter.variable``, ``time.step``, ``vertical.level``
- the raw GRIB keys as ``metadata.<key>``, e.g. ``metadata.shortName``

The values have the Python types they were stored with (e.g. ``time.step`` is a ``datetime.timedelta``). A key that is absent for a message is not in its ``dict``. A ``ValueError`` is raised if the file is not in the database.

.. code-block:: python

    for row in db.rows("data1.grib"):
        print(row["_offset"], row["_length"], row["parameter.variable"], row["vertical.level"])

    # 0 234 t 1000
    # 240 234 t 850
    # 480 234 t 700
    # ...

    db.close()

Using the database with a fieldlist
===================================

A database prepared with ``GribIndex`` can be used by ``to_fieldlist()``. When ``index`` is the path of the database, the database is reused without scanning the GRIB files again, as long as the files are unchanged and the ``index_extra_keys`` were already scanned for them (see :ref:`grib-index`).

.. code-block:: python

    import earthkit.data as ekd
    from earthkit.data.readers.grib.index import GribIndex

    # prepare the database
    with GribIndex.open(["data1.grib", "data2.grib"], db_path="my_index.db"):
        pass

    # build the fieldlist from it
    ds = ekd.from_source("file", ["data1.grib", "data2.grib"])
    fl = ds.to_fieldlist(index="my_index.db")
    len(fl)  # 12

Errors
======

- ``ValueError`` when an existing database was created with another version of the schema. Remove the file to recreate it.
- ``ValueError`` when ``rows()`` or ``extra_keys()`` is used with a file that is not in the database.
- ``ValueError`` from ``cache_db_path()``, ``find_in_cache()``, ``open()`` and ``from_file()`` (both without ``db_path``) when the :ref:`cache-policy <cache_policies>` is "off", and from ``open()`` when more than one file is given without ``db_path``.

See also
========

- :ref:`grib-index`
- :ref:`/tutorials/grib/grib_metadata_index.ipynb`
- :ref:`caching`
- :ref:`cache_policies`
