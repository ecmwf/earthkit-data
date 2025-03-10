.. _grib-metadata-cache

GRIB field metadata caching
//////////////////////////////

The ``use-grib-metadata-cache`` :ref:`config option <config>` controls whether :ref:`grib` fields will cache their metadata access. The default value is ``True``.

This is an in-memory cache attached to the field and implemented for the low-level metadata accessor for individual keys. Getting the values from the cache can be significantly faster than reading them from the GRIB handle, even when the handle is kept in memory.

This config option is applied to all the different GRIB field types, even for fields stored entirely in memory (see :ref:`grib-memory`).


Overriding the configuration
++++++++++++++++++++++++++++

In addition to changing the :ref:`config`, it is possible to override ``use-grib-metadata-cache`` when loading a given fieldlist by passing the ``use_grib_metadata_cache`` keyword argument (note the underscores) to :func:`from_source`. When this kwarg is not specified in :func:`from_source` or is set to None, its value is taken from the actual :ref:`config`. E.g.:

.. code-block:: python

    import earthkit.data as ekd

    # will override the config
    ds = ekd.from_source(
        "file",
        "test6.grib",
        use_grib_metadata_cache=False,
    )
