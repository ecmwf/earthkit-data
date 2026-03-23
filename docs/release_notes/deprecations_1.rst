Migration guide for 1.0.0
============================


from_source
----------------

The returned object
+++++++++++++++++++++++

The return type of the :func:`from_source` function was changed and now it returns a :py:class:`Data` object. This object provides some basic information about the data but its primary goal is to convert it to a given representation for further work. The actual data loading is deferred as much as possible, until the data is converted into a given type.

For example, when we read GRIB data with :func:`from_source`, it returns a data object that can be converted to a fieldlist with :meth:`to_fieldlist`. Previously, :func:`from_source` returned a fieldlist directly. E.g.:

Old way:

.. code-block:: python

    import earthkit.data as ekd

    fl = ekd.from_source("file", "test6.grib")

New way:

.. code-block:: python

    import earthkit.data as ekd

    fl = ekd.from_source("file", "test6.grib").to_fieldlist()


The available conversion types can be quickly accessed by calling :py:attr:`Data.available_types` on the returned object. E.g.:

.. code-block:: python

    import earthkit.data as ekd

    data = ekd.from_source("file", "test6.grib")
    print(data.available_types)
    ['fieldlist', 'xarray', 'numpy']


Examples:

 -  :ref:`/examples/source/data.ipynb`


The ``read_all`` kwarg
+++++++++++++++++++++++

Previously, we could use the ``read_all`` kwarg in :func:`from_source` when ``stream=True`` was also set (this latter is only available in sources supporting streams). This is now removed and the same functionality can be achieved by passing ``read_all`` as a kwarg to :func:`to_fieldlist`. E.g.:


Old way:

.. code-block:: python

    import earthkit.data as ekd

    url = "https://sites.ecmwf.int/repository/earthkit-data/examples/test.grib"
    fl = ekd.from_source("url", url, stream=True, read_all=True)

New way:

.. code-block:: python

    import earthkit.data as ekd

    url = "https://sites.ecmwf.int/repository/earthkit-data/examples/test.grib"
    fl = ekd.from_source("url", url, stream=True).to_fieldlist(read_all=True)


See more details in :ref:`streams_read_all`.



Concatenation
---------------

Previously, fiedllists and some sources could be concatenated using the ``+`` operator. This has been replaced with the ``concat`` function:

.. code-block:: python

    from earthkit.data import concat

    ds3 = concat(ds1, ds2)

Please note that ``+`` operator is used an arithmetic operator for Fields and Fieldlists, so it is still available but with a different meaning.


Field
-----------

The Field API has been redesigned and many methods have been removed or changed. The following table gives an overview of the changes in the Field API:

.. list-table::
   :header-rows: 1
   :widths: 22 13 65

   * - Old API
     - New API
     - Notes
   * - to_numpy()
     - to_numpy()
     - New kwarg: ``copy=True``
   * - to_array()
     - to_array()
     - New kwarg: ``copy=True``
   * - to_latlon()
     - N/A
     - Use :func:`f.geography.latlons`. This returns a tuple of arrays (lats, lons).
   * - to_points()
     - N/A
     - Use: :func:`f.geography.points`, :func:`f.geography.xys`. These functions return a tuple of arrays (x, y)
   * - grid_points()
     - N/A
     - Use: :func:`f.geography.latlons`.  This returns a tuple of arrays (lats, lons).
   * - projection()
     - N/A
     - Use: :func:`f.geography.projection`
   * - bounding_box()
     - N/A
     - Use: :func:`f.geography.bounding_box`
   * - clone()
     - N/A
     - Functionality not needed. Use :func:`f.set` instead
   * - copy()
     - N/A
     - Functionality not needed. Use :func:`f.set` instead
   * - as_namespace()
     - N/A
     -
   * - datetime()
     - N/A
     - Use :func:`f.time.base_datetime` and :func:`f.time.valid_datetime` instead.
   * - valid_datetime()
     - N/A
     - Use :func:`f.time.valid_datetime`
   * - base_datetime()
     - N/A
     - Use :func:`f.time.base_datetime`
   * - metadata()
     - metadata()
     - Has limited scope now. Can only access keys in the raw metadata belonging to the object the field was created from. E.g. for GRIB this works:

        .. code-block:: python

           f.metadata("shortName")
           f.metadata("metadata.shortName")


        When the key does not exist in the raw metadata, it raises a KeyError.
   * - MetaData object accessed by calling metadata() without args/kwargs
     - N/A
     -
   * - dump()
     - N/A
     - Use: :func:`f.describe`
   * - describe()
     - Still exists but functionality changed.
     -
   * - handle
     - N/A
     -
   * - mars_area
     - N/A
     - Use: :func:`f.geography.area`
   * - mars_grid
     - N/A
     -
   * - resolution
     - N/A
     -
   * - rotation
     - N/A
     - N/A
   * - grid_points_unrotated()
     - N/A
     - N/A
   * - save()
     - N/A
     - Use: :func:`f.to_target`
   * - write()
     - N/A
     - Use: :func:`f.to_target`


Fieldlist
-----------

The Field API has been redesigned and many methods have been removed or changed. The following table gives an overview of the changes in the Field API:


.. list-table::
   :header-rows: 1
   :widths: 28 38 34

   * - Old API
     - New API
     - Notes
   * - to_numpy()
     - to_numpy()
     - New kwarg: ``copy=True``
   * - to_array()
     - to_array()
     - New kwarg: ``copy=True``
   * - to_latlon()
     - N/A
     - Use :func:`fl.geography.latlons`. This returns a tuple of arrays (lats, lons)
   * - to_points()
     - N/A
     - Use: :func:`fl.geography.points`, :func:`fl.geography.xys`. These functions return a tuple of arrays (x, y)
   * - projection()
     - N/A
     - Use: :func:`fl.geography.projection`
   * - bounding_box()
     - N/A
     - Use: :func:`fl.geography.bounding_box`
   * - datetime()
     - N/A
     -
   * - metadata()
     - metadata()
     - Has limited scope now. Can only access keys in the raw metadata belonging to the object the field was created from. E.g. for GRIB this works:

        .. code-block:: python

           f.metadata("shortName")
           f.metadata("metadata.shortName")


        When the key does not exist in the raw metadata, it raises a KeyError.
   * - save()
     - N/A
     - Use: :func:`f.to_target`
   * - write()
     - N/A
     - Use: :func:`f.to_target`
