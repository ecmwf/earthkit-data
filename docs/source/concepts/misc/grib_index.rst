.. _grib-index:

GRIB metadata index
//////////////////////////////

When a GRIB file is read, earthkit-data has to scan all its messages to find out what fields it contains. For many or large files this can be slow. The **GRIB metadata index** scans the GRIB files **once**, stores the metadata of every message in a small `sqlite <https://www.sqlite.org>`_ database, and then builds the fieldlist from that database **without reading the GRIB files**. The files are only opened again when the field values (or a metadata key that is not stored in the database) are needed.

The index is switched on with the ``index`` option of ``to_fieldlist()``. See the :ref:`/tutorials/grib/grib_metadata_index.ipynb` notebook for a worked example.

Using the index
===============

Index stored in the cache
+++++++++++++++++++++++++

With ``index=True`` each GRIB file gets its own database in the earthkit-data :ref:`cache <caching>`. This requires the :ref:`cache-policy <cache_policies>` to be "user" or "temporary". With the default policy ("off") a ``ValueError`` is raised.

.. code-block:: python

    import earthkit.data as ekd

    ekd.config.set("cache-policy", "user")

    ds = ekd.from_source("file", "data.grib")
    fl = ds.to_fieldlist(index=True)

The result is a normal fieldlist, which can be used as usual (``sel()``, ``get()``, ``to_xarray()`` etc.). While a file is being scanned a progress bar is shown.

Index stored in a file
++++++++++++++++++++++

When ``index`` is a path, the database is stored in that file. It is created when it does not exist yet. One database can hold any number of GRIB files, so this is the way to index several files together. The data can be a single file, a list of files or a directory:

.. code-block:: python

    import earthkit.data as ekd

    # one file
    ds = ekd.from_source("file", "data1.grib")
    fl = ds.to_fieldlist(index="my_index.db")

    # a list of files in the same database
    ds = ekd.from_source("file", ["data1.grib", "data2.grib"])
    fl = ds.to_fieldlist(index="my_index.db")

    # all the files of a directory
    ds = ekd.from_source("file", "my_grib_dir")
    fl = ds.to_fieldlist(index="my_index.db")

Storing extra keys
++++++++++++++++++

The database stores the metadata of the fieldlist components (e.g. ``parameter.variable``, ``time.step``, ``vertical.level``) and a set of raw GRIB keys, which are available as ``metadata.<key>`` (see :ref:`below <grib-index-what-is-stored>`). Other GRIB keys can be added with ``index_extra_keys``. They are ignored when ``index`` is not set.

.. code-block:: python

    import earthkit.data as ekd

    ds = ekd.from_source("file", "data.grib")
    fl = ds.to_fieldlist(index="my_index.db", index_extra_keys=["bitsPerValue"])
    fl.get("metadata.bitsPerValue")

Reuse and re-scan
=================

An existing database is not scanned again when it is still valid, but what "valid" means depends on how the index is stored.

Index stored in a file (``index=<path>``)
+++++++++++++++++++++++++++++++++++++++++

The database is looked up by its path and only the requested input files are checked. Other files that may already be in a shared database are not validated. A requested file is **reused** when its size and modification time are the same as when it was scanned, and all the requested ``index_extra_keys`` were already scanned for it. Otherwise the file is **re-scanned inside the same database**: a changed file replaces its old entry, a new file is added, and a file missing some extra keys is scanned again with the old and the new keys. A file is scanned and stored in a single transaction, so a failure leaves the database as it was.

Index stored in the cache (``index=True``)
++++++++++++++++++++++++++++++++++++++++++

The name of the database in the cache is computed from the path of the GRIB file, its timestamps and size, the extra keys, and the version of the database schema. Nothing is re-scanned inside such a database. Instead, a changed file or a different set of ``index_extra_keys`` simply selects **another database** (which is then created), and the old one is no longer used. The databases are files in the cache, so they live as long as the cache does (see :ref:`cache policies <cache_policies>`).

.. _grib-index-what-is-stored:

What comes from the database
============================

An indexed fieldlist behaves like a normal one. The difference is where the information comes from.

Answered from the database, without reading the GRIB file:

- the keys of the fieldlist components (``parameter.*``, ``time.*``, ``vertical.*``, ``ensemble.*``, ``geography.*`` etc.)
- the raw GRIB keys stored in the database (unless ``astype`` is used, see below), which are available as ``metadata.<key>``: the keys of the ``mars`` namespace of the message, a default set of commonly used keys (e.g. ``shortName``, ``paramId``, ``typeOfLevel``, ``level``, ``date``, ``time``, ``step``, ``gridType``, ``edition``) and the ``index_extra_keys``. A stored key that a message does not have is reported as missing, again without reading the file
- the number of fields and the position of each message in the file

Still reading the GRIB file when needed:

- the **values** are always read lazily from the file
- **any other GRIB key**, which is not stored in the database, is read from the message in the file
- a stored raw key (``metadata.<key>``) requested with an ``astype`` that is not the type it is stored with. The stored values have the native type of the key, e.g. ``int`` for ``level``, so ``get("metadata.level")`` and ``get("metadata.level", astype=int)`` are answered from the database, but ``get("metadata.level", astype=str)`` reads the message from the file. This does not apply to a stored key that a message does not have, which is reported as missing without reading the file
- the **geography** of grids that have no grid specification (``gridSpec``), e.g. Mercator. The shape of the grid is stored, but the latitudes and longitudes are read from the file the first time they are needed. For grids with a grid specification no file access is needed
- the **coefficients of hybrid levels** are read from the file the first time they are used. Other level types need no file access

Xarray
++++++

When the fieldlist is converted to Xarray with ``add_earthkit_attrs=False``, no GRIB file is read until the data are loaded (e.g. with ``.load()``) for grids with a grid specification. For grids without one (see above) the latitudes and longitudes are read from the file once for each distinct grid. By default, one GRIB message per variable is read to get the earthkit attributes.

.. code-block:: python

    import earthkit.data as ekd

    ds = ekd.from_source("file", "data.grib")
    fl = ds.to_fieldlist(index="my_index.db")

    # no GRIB file is read here for grids with a grid specification
    # (otherwise the grid is read once from the file) ...
    ds_xr = fl.to_xarray(add_earthkit_attrs=False)

    # ... and the values are only read when the data are loaded
    ds_xr.load()

Limits
======

- The index works with GRIB data stored in **local files**. It is not available for data read as a stream.
- ``index`` cannot be combined with the ``parts`` argument. A ``ValueError`` is raised.
- A database created with another version of the schema cannot be used. A ``ValueError`` is raised and the database file has to be removed to be recreated.
- ``index=True`` needs the :ref:`cache-policy <cache_policies>` to be "user" or "temporary", otherwise a ``ValueError`` is raised. Use a path instead if the cache is not enabled.
- The earthkit-data :ref:`cache <caching>` is intended to be used by a single user.

How it works
============

The index is implemented by the :py:class:`~earthkit.data.readers.grib.index.GribIndex` class. It opens (or creates) the sqlite database, scans the GRIB files that are not up to date, and gives access to the stored rows. ``to_fieldlist(index=...)`` uses it internally, so there is usually no need to use it directly (see :ref:`grib-index-object` for how to use the class to inspect or prepare databases). The fieldlist reads the stored rows when it is first used and then closes the database. The GRIB files are opened again only for the cases described above.

The database has three tables:

- ``meta``: general information, currently only the schema version
- ``paths``: one row for each GRIB file, with its path, the size and modification time it had when it was scanned (used to detect changes) and the extra keys scanned for it
- ``grib_index``: one row for each GRIB message, with the file it belongs to, its offset and length in the file, and one column for each stored key (the component keys and the ``metadata.<key>`` raw keys). The columns are added when they are first needed, so one database can hold files with different sets of keys

A SQL NULL value in ``grib_index`` means that the key is absent for that message.

See also
========

- :ref:`grib-index-object`
- :ref:`/tutorials/grib/grib_metadata_index.ipynb`
- :ref:`caching`
- :ref:`cache_policies`
