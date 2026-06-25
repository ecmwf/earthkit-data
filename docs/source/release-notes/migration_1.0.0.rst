.. _migration_1.0.0:

Migration guide for 1.0
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

 -  :ref:`/tutorials/source/data.ipynb`


The ``read_all`` kwarg
+++++++++++++++++++++++

Previously, we could use the ``read_all`` kwarg in :func:`from_source` when ``stream=True`` was also set (this latter is only available in sources supporting streams). This is now removed and the same functionality can be achieved by passing ``read_all`` as a kwarg to :func:`to_fieldlist`. E.g.:


Old way:

.. code-block:: python

    import earthkit.data as ekd

    url = "https://sites.ecmwf.int/repository/earthkit-data/tutorials/test.grib"
    fl = ekd.from_source("url", url, stream=True, read_all=True)

New way:

.. code-block:: python

    import earthkit.data as ekd

    url = "https://sites.ecmwf.int/repository/earthkit-data/tutorials/test.grib"
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

Field modification
++++++++++++++++++++++++

Fields can be modified using the :py:meth:`~earthkit.data.core.field.Field.set` method. This method allows to set new data values and/or change  metadata keys. See the notebook examples:

- :ref:`/tutorials/grib/grib_modify_metadata.ipynb`
- :ref:`/tutorials/grib/grib_modify_values.ipynb`

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

- :ref:`/tutorials/field/field_overview.ipynb`


Changes in the Field API
++++++++++++++++++++++++


The Field API has been redesigned and many methods have been removed or changed. The following table gives an overview of the changes in the Field API (the ``f`` in the table below is a :py:class:`~earthkit.data.core.field.Field` object):

.. list-table::
   :header-rows: 1
   :widths: 22 13 65

   * - Old API
     - New API
     - Notes
   * - to_numpy()
     - :py:meth:`~earthkit.data.core.field.Field.to_numpy`
     - New kwarg added: ``copy=True``. By default returns a copy of the data array.
   * - to_array()
     - :py:meth:`~earthkit.data.core.field.Field.to_array`
     - New kwarg added: ``copy=True``. By default returns a copy of the data array.
   * - to_latlon()
     - :func:`f.geography.latlons`
     - The new function returns a tuple of arrays (lats, lons)
   * - to_points()
     - :func:`f.geography.points` or :func:`f.geography.xys`
     - The new functions return a tuple of arrays (x, y)
   * - grid_points()
     - :func:`f.geography.latlons`
     - The new function returns a tuple of arrays (lats, lons).
   * - projection()
     - :func:`f.geography.projection`
     -
   * - bounding_box()
     - :func:`f.geography.bounding_box`
     -
   * - clone()
     - N/A
     - Functionality not needed. Use :py:meth:`~earthkit.data.core.field.Field.set` instead
   * - copy()
     - N/A
     - Functionality not needed. Use :py:meth:`~earthkit.data.core.field.Field.set` instead
   * - as_namespace()
     - :py:meth:`~earthkit.data.core.field.Field.get` with the ``collections`` kwarg
     - Use e.g. ``f.get(collections="metadata.mars")`` to get the "mars" ecCodes namespace. Only available for GRIB data.
   * - datetime()
     - N/A
     - Use :func:`f.time.base_datetime` and :func:`f.time.valid_datetime` instead.
   * - valid_datetime()
     - :func:`f.time.valid_datetime`
     - The new function returns a `datetime.datetime` object.
   * - base_datetime()
     - :func:`f.time.base_datetime`
     - The new function returns a `datetime.datetime` object.
   * - metadata()
     - :py:meth:`~earthkit.data.core.field.Field.metadata`
     - Has limited scope now. Can only access keys in the raw metadata belonging to the object the field was created from. E.g. for GRIB this works:

        .. code-block:: python

           f.metadata("shortName")
           f.metadata("metadata.shortName")


        When the key does not exist in the raw metadata, it raises a KeyError.
   * - MetaData object accessed by calling metadata() without args/kwargs
     - N/A
     - This object is no longer available. The field itself provides the same functionality through :py:meth:`~earthkit.data.core.field.Field.get` and :py:meth:`~earthkit.data.core.field.Field.set`.
   * - dump()
     - N/A
     - Use :py:meth:`~earthkit.data.core.field.Field.describe` instead.
   * - describe()
     - Still exists but functionality changed.
     -
   * - handle
     - N/A
     - The handle is no longer available. Use :py:meth:`~earthkit.data.core.field.Field.get` or :py:meth:`~earthkit.data.core.field.Field.metadata` to access the raw metadata keys.
   * - mars_area
     - N/A
     - Use: :func:`f.geography.area`
   * - mars_grid
     - N/A
     - Use: :func:`f.geography.grid`
   * - resolution
     - N/A
     - This is no longer available.
   * - rotation
     - N/A
     - This is no longer available.
   * - grid_points_unrotated()
     - N/A
     - This is no longer available.
   * - save()
     - :py:meth:`~earthkit.data.core.field.Field.to_target`
     -
   * - write()
     - :py:meth:`~earthkit.data.core.field.Field.to_target`
     -


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

The following table gives an overview of the changes in the Fieldlist API (the ``fl`` in the table below is a :py:class:`~earthkit.data.fieldlist.FieldList` object):

.. list-table::
   :header-rows: 1
   :widths: 28 38 34

   * - Old API
     - New API
     - Notes
   * - to_numpy()
     - :py:meth:`~earthkit.data.fieldlist.FieldList.to_numpy`
     - New kwarg added: ``copy=True``. By default returns a copy of the data array.
   * - to_array()
     - :py:meth:`~earthkit.data.fieldlist.FieldList.to_array`
     - New kwarg added: ``copy=True``. By default returns a copy of the data array.
   * - to_latlon()
     - :func:`fl.geography.latlons`
     - The new function returns a tuple of arrays (lats, lons)
   * - to_points()
     - :func:`fl.geography.points` or :func:`fl.geography.xys`
     - These functions return a tuple of arrays (x, y)
   * - projection()
     - :func:`fl.geography.projection`
     -
   * - bounding_box()
     - :func:`fl.geography.bounding_box`
     -
   * - datetime()
     - N/A
     - This method is no longer available. Use the following instead:

        .. code-block:: python

           f.get("time.base_datetime")
           f.get("time.valid_datetime")

   * - metadata()
     - :py:meth:`~earthkit.data.fieldlist.FieldList.metadata`
     - Has limited scope now. Can only access keys in the raw metadata belonging to the object the field was created from. E.g. for GRIB this works:

        .. code-block:: python

           f.metadata("shortName")
           f.metadata("metadata.shortName")


        When the key does not exist in the raw metadata, it raises a KeyError.
   * - save()
     - :py:meth:`~earthkit.data.fieldlist.FieldList.to_target`
     -
   * - write()
     - :py:meth:`~earthkit.data.fieldlist.FieldList.to_target`
     -


Indexed mode removed
+++++++++++++++++++++

The GRIB indexed mode, previously available via the ``indexing=True`` kwarg in
:py:func:`~earthkit.data.from_source`, has been removed:

.. code-block:: python

    # No longer supported
    fl = ekd.from_source("file", "data.grib", indexing=True)

In indexed mode the GRIB file was pre-scanned and all field metadata was stored in an
in-memory index, making repeated :meth:`sel` and :meth:`order_by` calls faster for large
files at the cost of upfront indexing time and additional memory. This feature will be
reimplemented in a future release, potentially with a different interface.


Xarray engine
------------------

The Xarray engine has been refactored and many of the internal classes and methods have been changed. The following list gives an overview of the changes in the Xarray engine:

- a new default profile :ref:`earthkit <xr_profile_earthkit>` has been added which is used when no profile is specified. This profile is designed to work with the new format independent metadata keys from :py:class:`~earthkit.data.core.field.Field` to generate the Xarray dataset.
- the old  :ref:`mars <xr_profile_mars>` and :ref:`grib <xr_profile_grib>` profiles were kept but they are now using some of the new format independent metadata keys to generate the Xarray dataset.
- the "number" ``dim_role`` was renamed to "member" in line with the new format independent metadata keys. See: :ref:`xr_dim` for more details.
- the ``time_dim_mode`` kwarg in :func:`to_xarray` was replaced by ``time_dims`` and the meaning of some temporal dimensions in the ``dim_roles`` also changed.  See :ref:`xr_time_dims` for more details.
