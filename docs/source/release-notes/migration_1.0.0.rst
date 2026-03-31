.. _migration_1.0.0:

Migration guide for 1.0.0
============================

from_source
----------------

The returned object
+++++++++++++++++++++++

The return type of the :func:`from_source` function was changed and now it returns a :ref:`data object <data-object>` object. This object provides some basic information about the data but its primary goal is to convert it to a given representation for further work. The actual data loading is deferred as much as possible, until the data is converted into a given type.

For example, when we read GRIB data with :func:`from_source`, it returns a data object that can be converted to a fieldlist with :meth:`to_fieldlist`. Previously, :func:`from_source` returned a fieldlist directly. E.g.:

Old way:

.. code-block:: python

    import earthkit.data as ekd

    fl = ekd.from_source("file", "test6.grib")

New way:

.. code-block:: python

    import earthkit.data as ekd

    fl = ekd.from_source("file", "test6.grib").to_fieldlist()


The list of available conversion types can be quickly get by calling :py:attr:`Data.available_types` on the returned object. E.g.:

.. code-block:: python

    import earthkit.data as ekd

    data = ekd.from_source("file", "test6.grib")
    print(data.available_types)
    ['fieldlist', 'xarray', 'pandas', 'numpy']

Then we can call any of the corresponding ``to_*`` methods to convert the data to the desired type. E.g. to convert to an Xarray Dataset we can do:


.. code-block:: python

    import earthkit.data as ekd

    data = ekd.from_source("file", "test6.grib")
    ds = data.to_xarray()


Examples:

 -  :ref:`/how-tos/source/data.ipynb`


The ``read_all`` kwarg
+++++++++++++++++++++++

Previously, we could use the ``read_all`` kwarg in :func:`from_source` when ``stream=True`` was also set (this latter is only available in sources supporting streams). This is now removed and the same functionality can be achieved by passing ``read_all`` as a kwarg to :func:`to_fieldlist`. E.g.:


Old way:

.. code-block:: python

    import earthkit.data as ekd

    url = "https://sites.ecmwf.int/repository/earthkit-data/how-tos/test.grib"
    fl = ekd.from_source("url", url, stream=True, read_all=True)

New way:

.. code-block:: python

    import earthkit.data as ekd

    url = "https://sites.ecmwf.int/repository/earthkit-data/how-tos/test.grib"
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

The :py:class:`~earthkit.data.core.field.Field` is now not polymorphic but is made up of polymorphic components using format independent metadata. So far the following components are implemented:

- parameter (see: :py:class:`~earthkit.data.field.component.parameter.ParameterBase`)
- time (see: :py:class:`~earthkit.data.field.component.time.TimeBase`)
- vertical (see: :py:class:`~earthkit.data.field.component.vertical.VerticalBase`)
- geography (see: :py:class:`~earthkit.data.field.component.geography.GeographyBase`)
- ensemble (see: :py:class:`~earthkit.data.field.component.ensemble.EnsembleBase`)
- proc (see: :py:class:`~earthkit.data.field.component.proc.ProcBase`)
- labels (see: :py:class:`~earthkit.data.field.handler.labels.SimpleLabels`)

Each component has its own set of metadata keys and methods. There are two ways to access the related values from the components:

.. code-block:: python

    # use the get() method
    f.get("time.base_datetime")

    # use the key method on the component
    f.time.base_datetime()

Raw metadata keys are still available but they are only accessible either by using the "metadata." prefix in :func:`get` or through the :func:`metadata` method. E.g. if the :py:class:`~earthkit.data.core.field.Field` was created from a GRIB message, we can access the "shortName" key from the raw metadata like this:

.. code-block:: python

    f.get("metadata.shortName")
    f.metadata("shortName")
    f.metadata("metadata.shortName")


Field arithmetic
++++++++++++++++++++++++

Added :py:class:`~earthkit.data.core.field.Field` arithmetic. The basic maths operators can now be used to perform arithmetic operations on fields. The operations are performed on the data arrays of the fields, and the resulting field has the same metadata as the left operand and will be entirely stored in memory. For example:

.. code-block:: python

    f3 = f1 + f2
    f4 = f1 - f2
    f5 = f1 * f2
    f6 = f1 / f2


Notebook examples
++++++++++++++++++++++++

- :ref:`/how-tos/field/overview.ipynb`


Changes in the Field API
++++++++++++++++++++++++


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

FieldList arithmetic
++++++++++++++++++++++++

Added :py:class:`~earthkit.data.fieldlist.FieldList` arithmetic. The basic maths operators can now be used to perform arithmetic operations on fieldlists. The operations are performed on the data arrays of the fieldlists, and the resulting fieldlist has the same metadata as the left operand and will be entirely stored in memory. For example:

.. code-block:: python

    fl3 = fl1 + fl2
    fl4 = fl1 - fl2
    fl5 = fl1 * fl2
    fl6 = fl1 / fl2



Changes in the FieldList API
++++++++++++++++++++++++++++++

The following table gives an overview of the changes in the Fieldlist API:

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
     - Use :func:`fl.time.base_datetime` and :func:`fl.time.valid_datetime` instead.
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


Xarray engine
------------------

The Xarray engine has been refactored and many of the internal classes and methods have been changed. The following table gives an overview of the changes in the Xarray engine:

- a new default profile :ref:`earthkit <xr_profile_earthkit>` has been added which is used when no profile is specified. This profile is designed to work with the new format independent metadata keys from :py:class:`~earthkit.data.core.field.Field` to generate the Xarray dataset.
- the old  :ref:`mars <xr_profile_mars>` and :ref:`grib <xr_profile_grib>` profiles were kept but they are now using some of the new format independent metadata keys to generate the Xarray dataset.
- the "number" ``dim_role`` was renamed to "member" in line with the new format independent metadata keys. See: :ref:`xr_dim` for more details.
