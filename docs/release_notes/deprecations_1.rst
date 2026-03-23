Migration guide for 1.0.0
============================


from_source
----------------

Returned data object
+++++++++++++++++++++++

The :func:`from_source` function now returns a **data object**. This object provides some basic information about the data but its primary goal is to convert it to a given representation for further work. The actual data loading is deferred as much as possible, until the data is converted into a given type.

For example, when we read GRIB data with :func:`from_source`, it returns a data object that can be converted to a fieldlist with :meth:`to_fieldlist`. Previously, :func:`from_source` returned a fieldlist directly. E.g.:

Old way:

.. code-block:: python

    import earthkit.data as ekd

    fl = ekd.from_source("file", "test6.grib")

New way:

.. code-block:: python

    import earthkit.data as ekd

    fl = ekd.from_source("file", "test6.grib").to_fieldlist()


The read_all kwarg
+++++++++++++++++++++++

Previously, data sources supporting streams had the ``read_all`` kwarg in :func:`from_source`. This is now removed and the same functionality can be achieved by passing ``read_all`` as a kwarg to :func:`from_source` directly. E.g.:


When set to ``True``, the returned data object will read all the data from the source and keep it in memory, so that it can be converted to a fieldlist multiple times without re-reading the source. When set to ``False`` (default), the returned data object will read only metadata from the source and defer reading the actual data until conversion to a fieldlist. In this case, once a fieldlist is generated, the source is consumed and cannot be used again for another conversion. E.g.:

Concatenation
---------------

Previously, concatenation used the ``+`` operator. This has been replaced with the ``concat`` function:

.. code-block:: python

    from earthkit.data import concat

    ds3 = concat(ds1, ds2)


Field
-----------

The Field API has been redesigned and many methods have been removed or changed. The following tables give an overview of the changes in the Field API:

.. list-table::
   :header-rows: 1
   :widths: 22 13 65

   * - Old API
     - New API
     - Remark
   * - values
     - values
     -
   * - to_numpy()
     - to_numpy()
     - Has copy=True kwarg now
   * - to_array()
     - to_array()
     - Has copy=True kwarg now
   * - to_latlon()
     - N/A
     - Use f.geography.latlons()

       Returns tuple of arrays
   * - to_points()
     - N/A
     - Use: f.geography.points(), f.geography.xys()

       Returns tuple of arrays
   * - grid_points()
     - N/A
     - Use: f.geography.latlons()

       Returns tuple of arrays
   * - projection()
     - N/A
     - Use: f.geography.projection()
   * - bounding_box()
     - N/A
     - Use: f.geography.bounding_box()
   * - clone()
     - N/A
     - Functionality not needed.

       Use "set()" instead
   * - copy()
     - N/A
     - Functionality not needed.

       Use "set()" instead
   * - as_namespace()
     - N/A
     -
   * - datetime()
     - N/A
     - f.time.base_datetime()

       f.time.valid_datetime()
   * - valid_datetime()
     - N/A
     - Use the f.time.valid_datetime()

       instead
   * - base_datetime()
     - N/A
     - Use the f.time.base_datetime()

       instead
   * - metadata()
     - metadata()
     - Has now limited scope. Can only access keys in the raw metadata belonging to the object the field was created from. E.g. for GRIB this works:

       f.metadata("shortName")

       But this does not (high level key):

       f.metadata("parameter.variable")
   * - MetaData object accessed buy calling metadata() without args/kwargs
     - N/A
     -
   * -
     - get()
     - f.get("parameter.variable")

       f.get(metadata.shortName")
   * - dump()
     - N/A
     - Use: f.describe()
   * - describe()
     - Still there but functionality changed. Similar to dump() before
     -
   * - message()
     - message()
     -
   * - handle
     - N/A
     -
   * - mars_area
     - N/A
     - Use: f.geography.area()
   * - mars_grid
     - N/A
     -
   * - resolution
     - N/A
     - N/A
   * - rotation
     - N/A
     - N/A
   * - grid_points_unrotated()
     - N/A
     - N/A
   * - save()
     - N/A
     - to_target()
   * - write()
     - N/A
     - to_target()


Fieldlist
-----------

.. list-table::
   :header-rows: 1
   :widths: 28 38 34

   * - Old API
     - New API
     - Remark
   * - values
     - values
     -
   * - data()
     - data()
     -
   * - to_numpy()
     - to_numpy()
     - Has copy=True kwarg now
   * - to_array()
     - to_array()
     - Has copy=True kwarg now
   * - to_latlon()
     - N/A
     - Use fl.geography.latlons()

       Returns tuple of arrays
   * - to_points()
     - N/A
     - Use: fl.geography.points(), fl.geography.xys()

       Returns tuple of arrays
   * - projection()
     - N/A
     - Use: fl.geography.projection()
   * - bounding_box()
     - N/A
     - Use: fl.geography.bounding_box()
   * -
     - geography
     - Returns the geography component of the first field, if all the fields have the same geography. Raises exception otherwise.
   * - datetime()
     - N/A
     -
   * - metadata()
     - metadata()
     - Has now limited scope. Can only access keys in the raw metadata belonging to the object the field was created from. E.g. for GRIB this works:

       fl.metadata("shortName")

       But this does not (high level key):

       fl.metadata("parameter.variable")
   * -
     - get()
     - fl.get("parameter.variable")

       fl.get(metadata.shortName")
   * - save()
     - N/A
     - to_target()
   * - write()
     - N/A
     - to_target()
   * - to_tensor()
     - to_tensor()
     -
   * - cube()
     - to_cube()
     -
