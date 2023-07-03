.. _grib:


GRIB
---------

GRIB is the WMO's format for binary gridded data consisting of GRIB messages, which in the earthkit terminology are called **fields**. The earthkit-data GRIB interface is based on :xref:`eccodes` and can handle both GRIB `edition 1 <https://community.wmo.int/activity-areas/wmo-codes/manual-codes/grib-edition-1>`_ and `edition 2 <https://library.wmo.int/index.php?lvl=notice_display&id=10684>`_.

Fieldlists
+++++++++++

We can read/retrieve GRIB data with :func:`from_source <data-sources>`. The resulting object will be a :obj:`FieldList <data.readers.grib.index.FieldList>` representing a list of :obj:`GribFields <data.readers.grib.codes.GribField>`, which we can iterate through:

.. code-block:: python

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")

    >>> len(ds)
    2

    >>> for f in ds:
    ...     print(f)
    ...
    GribField(2t,1000,20200513,1200,0,0)
    GribField(msl,1000,20200513,1200,0,0)


The following table gives an overview of the :obj:`FieldList API<data.readers.grib.index.FieldList>`:

.. list-table:: Highlights of the FieldList API
   :header-rows: 1

   * - Methods/Operators
     - API
   * - :ref:`conversion`
     - :meth:`to_xarray() <data.readers.grib.index.FieldList.to_xarray>`
   * - :ref:`concat`
     -
   * - :ref:`iter`
     -
   * - :ref:`slice`
     -
   * - :ref:`sel`
     - :meth:`sel() <data.readers.grib.index.FieldList.sel>`
   * - :ref:`order_by`
     - :meth:`order_by() <data.readers.grib.index.FieldList.order_by>`
   * - :ref:`data_values`
     - :meth:`to_numpy() <data.readers.grib.index.FieldList.to_numpy>`
   * - :ref:`metadata`
     - :meth:`metadata() <data.readers.grib.index.FieldList.metadata>`
   * - :ref:`inspection`
     - :meth:`ls() <data.readers.grib.index.FieldList.ls>`, :meth:`head() <data.readers.grib.index.FieldList.head>` and :meth:`tail() <data.readers.grib.index.FieldList.tail>`

Fields
+++++++

A :obj:`GribField <data.readers.grib.codes.GribField>` represent a single GRIB field. It primarily offers methods to:

 - :ref:`extract field values <data_values>`, such as :meth:`to_numpy() <data.readers.grib.codes.GribField.to_numpy>`
 - :ref:`extract field metadata <metadata>`, such as :meth:`metadata() <data.readers.grib.codes.GribField._metadata>`

Examples:

    - :ref:`/examples/grib_overview.ipynb`
    - :ref:`/examples/grib_metadata.ipynb`
    - :ref:`/examples/grib_selection.ipynb`
    - :ref:`/examples/grib_missing.ipynb`
