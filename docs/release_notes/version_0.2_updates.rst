Version 0.2 Updates
/////////////////////////


Version 0.2.0
===============


New features
++++++++++++++++

- added new source :ref:`data-sources-eod` to retrieve ECMWF open data. See the :ref:`/examples/ecmwf_open_data.ipynb` notebook example.
- added new method :func:`from_object` to use a objects like numpy arrays or xarray datasets as an input. See the :ref:`/examples/from_object.ipynb` notebook example.
- redesigned :ref:`bufr` handling. :ref:`bufr` data is now represented by a :class:`BUFRList <data.readers.bufr.bufr.BUFRList>` made up of :class:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>` objects. In many aspects it behaves similarly to a :obj:`FieldList <data.core.fieldlist.FieldList>` offering iteration, slicing, selection and message dump. For details see :ref:`here <bufr>` and also check the notebook examples:

     - :ref:`/examples/bufr_temp.ipynb`
     - :ref:`/examples/bufr_synop.ipynb`

- added the ``group_by`` option to :ref:`data-sources-fdb` stream source. With this option we can read data in groups from a stream. See the :ref:`/examples/fdb.ipynb` notebook example.
- changed how the field geography can be accessed. On a Field object we can now call the following methods:

   - :meth:`projection() <data.core.fieldlist.Field.projection>`: returns an object describing the projection. See the :ref:`/examples/projection.ipynb` notebook example.
   - :meth:`to_latlon() <data.core.fieldlist.Field.to_latlon>`: returns the latitudes and longitudes for all the gridpoints
   - :meth:`to_points() <data.core.fieldlist.Field.to_points>`: returns the geographical coordinates of all the gridpoints in the data's original Coordinate Reference System (CRS)

  The same methods can also be called on a :obj:`FieldList <data.core.fieldlist.FieldList>`:

     - when all the fields have the same grid geometry in the FieldList they return the value of the same function called on the first field
     - otherwise an exception is raised

- added new :ref:`settings` option ``reader-type-check-bytes`` to control the number of bytes read from the beginning of a source to identify its type. The default value is 64 and the allowed value range is [8, 4096]. (`#126 <https://github.com/ecmwf/earthkit-data/pull/126>`_)
- changed the return type of :meth:`FieldList.bounding_box() <data.core.fieldlist.FieldList.bounding_box>`, which now returns a list of bounding boxes (one per field). (`#122 <https://github.com/ecmwf/earthkit-data/issues/122>`_)
- removed options ``print`` and ``html`` from methods :meth:`FieldList.ls() <data.core.fieldlist.FieldList.ls>`, :meth:`FieldList.describe() <data.core.fieldlist.FieldList.describe>` and :meth:`GribField.dump() <data.readers.grib.codes.GribField.dump>`. Printing the resulting object can be simply done by using the Python ``print()`` method. (`#118 <https://github.com/ecmwf/earthkit-data/issues/118>`_)

Fixes
++++++

- fixed issue when :ref:`grib`, :ref:`bufr` or :ref:`odb` data contained extra bytes at the beginning :func:`from_source` could not identify their type. (`#123 <https://github.com/ecmwf/earthkit-data/issues/123>`_)
- fixed issue when not specifying the ``filter`` option in :func:`to_pandas` on :ref:`bufr` data caused a crash
