.. _grib:


GRIB
---------

GRIB is the WMO's format for binary gridded data consisting of GRIB messages, which in the earthkit terminology are called **fields**. The earthkit-data GRIB interface is based on :xref:`eccodes` and can handle both GRIB `edition 1 <https://community.wmo.int/activity-areas/wmo-codes/manual-codes/grib-edition-1>`_ and `edition 2 <https://library.wmo.int/index.php?lvl=notice_display&id=10684>`_ seamlessly.

Fieldsets
+++++++++++

We can read/retrieve GRIB data with :func:`from_source <data-sources>`. The resulting object will be a :obj:`FieldSet <data.readers.grib.index.FieldSet>` representing a list of :obj:`GribFields <data.readers.grib.codes.GribField>`, which we can iterate through:

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


The following table gives an overview of the :obj:`FieldSet API<data.readers.grib.index.FieldSet>`:

.. list-table:: Highlights of the FieldSet API
   :header-rows: 1

   * - Operation
     - Methods
   * - :ref:`iteration <iter>`
     -
   * - :ref:`slicing <slice>`
     -
   * - inspection
     - :meth:`FieldSet.ls() <data.readers.grib.index.FieldSet.ls>`, :meth:`FieldSet.head() <data.readers.grib.index.FieldSet.head>`
   * - :ref:`filtering <sel>`
     - :meth:`FieldSet.sel() <data.readers.grib.index.FieldSet.sel>`
   * - :ref:`ordering <order_by>`
     - :meth:`FieldSet.order_by() <data.readers.grib.index.FieldSet.order_by>`
   * - :ref:`field value <data_values>` and :ref:`metadata <metadata>` extraction
     - :meth:`FieldSet.to_numpy() <data.readers.grib.index.FieldSet.to_numpy>`, :meth:`FieldSet.metadata() <data.readers.grib.index.FieldSet.metadata>`
   * - :ref:`transforming <transform>` to other objects
     - :meth:`FieldSet.to_xarray() <data.readers.grib.index.FieldSet.to_xarray>`

Fields
+++++++

A :obj:`GribField <data.readers.grib.codes.GribField>`  represent a single GRIB field. It primarily offers methods to:

 - :ref:`extract field values <data-values>`, such as :meth:`GribField.to_numpy() <data.readers.grib.codes.GribField.to_numpy>`
 - :ref:`extract field metadata <metadata>`, such as :meth:`GribField.metadata() <data.readers.grib.codes.GribField._metadata>`

Examples:

    - :ref:`/examples/grib_overview.ipynb`
    - :ref:`/examples/grib_metadata.ipynb`
    - :ref:`/examples/grib_selection.ipynb`
    - :ref:`/examples/grib_missing.ipynb`
