Version 0.1 Updates
/////////////////////////


Version 0.1.4
===============


New features
++++++++++++++++

- added new source :ref:`data-sources-eod` to retrieve ECMWF open data. See the :ref:`/examples/ecmwf_open_data.ipynb` notebook example.
- redesigned :ref:`bufr` handling. :ref:`bufr` data is now represented by a :class:`BUFRList <data.readers.bufr.bufr.BUFRList>` made up of :class:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>` objects. In many aspects it behaves similarly to a :obj:`FieldList <data.readers.grib.index.FieldList>` offering iteration, slicing, selection and message dump. For details see :ref:`here <bufr>` and also check the notebook examples:

     - :ref:`/examples/bufr_temp.ipynb`
     - :ref:`/examples/bufr_synop.ipynb`

- added the ``group_by`` option to :ref:`data-sources-fdb` stream source. With this option we can read data in groups from a stream. See the :ref:`/examples/fdb.ipynb` notebook example. (`#109 <https://github.com/ecmwf/earthkit-data/pull/109>`_)
- added the :meth:`projection() <data.readers.grib.codes.GribField.projection>` method to Field objects. See the :ref:`/examples/projection.ipynb` notebook example.
- added the :meth:`to_latlon() <data.readers.grib.codes.GribField.to_latlon>` method to Field objects to return the latitudes and longitudes for all the gridpoints. At the same time the behaviour of :meth:`to_points() <data.readers.grib.codes.GribField.to_points>` was changed and it now returns the geographical coordinates in the data’s original Coordinate Reference System (CRS).
- added the :meth:`to_latlon() <data.readers.grib.index.FieldList.to_latlon>` to FieldLists to return the latitudes/longitudes shared by all the fields. When not all the fields have the same grid geometry it raises an exception.
- added new :ref:`settings` option ``reader‑type‑check‑bytes`` to control the number of bytes read from the beginning of a source to identify its type. The default value is 64 and the allowed value range is [8, 4096]. (`#126 <https://github.com/ecmwf/earthkit-data/pull/126>`_)
- changed the return type of :meth:`FieldList.bounding_box() <data.readers.grib.index.FieldList.bounding_box>`, which now returns a list of bounding boxes (one per field). (`#122 <https://github.com/ecmwf/earthkit-data/issues/122>`_)
- removed options ``print`` and ``html`` from methods :meth:`FieldList.ls() <data.readers.grib.index.FieldList.ls>`, :meth:`FieldList.describe() <data.readers.grib.index.FieldList.describe>` and :meth:`GribField.dump() <data.readers.grib.codes.GribField.dump>`. Printing the resulting object can be simply done by using the Python ``print()`` method. (`#118 <https://github.com/ecmwf/earthkit-data/issues/118>`_)

Fixes
++++++

- fixed issue when :ref:`grib`, :ref:`bufr` or :ref:`odb` data contained extra bytes at the beginning :func:`read_source` could not identify their type. (`#123 <https://github.com/ecmwf/earthkit-data/issues/123>`_)
- fixed issue when not specifying the ``filter`` option in :func:`to_pandas` on :ref:`bufr` data caused a crash
