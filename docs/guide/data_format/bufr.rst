.. _bufr:


BUFR
---------

BUFR (Binary Universal Form for Representation of meteorological data) is a binary data format maintained by WMO. The earthkit-data interface supports both BUFR `edition 3 <https://community.wmo.int/en/activity-areas/wmo-codes/manual-codes/bufr-edition-3-and-crex-edition-1>`_ and `edition 4 <https://library.wmo.int/index.php?lvl=notice_display&id=10684>`_.

BUFRList
+++++++++++

We can read/retrieve BUFR data with :func:`from_source <data-sources>`. The resulting object will be a :obj:`BUFRList <data.readers.bufr.bufr.BUFRList>` representing a list of :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>`, which we can iterate through:

.. code-block:: python

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/temp_10.bufr")

    >>> len(ds)
    10

    >>> for f in ds:
    ...     print(f)
    ...
    GribField(2t,1000,20200513,1200,0,0)
    GribField(msl,1000,20200513,1200,0,0)


The following table gives an overview of the :obj:`BUFRList API<data.readers.bufr.bufr.BUFRList>`:

.. list-table:: Highlights of the BUFRList API
   :header-rows: 1

   * - Methods/Operators
     - API
   * - :ref:`conversion`
     - :meth:`pandas() <data.readers.bufr.bufr.BUFRList.to_pandas>`
   * - :ref:`concat`
     -
   * - :ref:`iter`
     -
   * - :ref:`slice`
     -
   * - :ref:`sel`
     - :meth:`sel() <data.reader.bufr.bufr.BUFRList.sel>`
   * - :ref:`order_by`
     - :meth:`order_by() <data.reader.bufr.bufr.BUFRList.order_by>`
   * - :ref:`metadata`
     - :meth:`metadata() <data.reader.bufr.bufr.BUFRList.metadata>`
   * - :ref:`inspection`
     - :meth:`ls() <data.reader.bufr.bufr.BUFRList.ls>`, :meth:`head() <data.reader.bufr.bufr.BUFRList.head>`, :meth:`tail() <data.reader.bufr.bufr.BUFRList.tail>`

BUFRMessage
++++++++++++++

A :obj:`GribField data.reader.bufr.bufr.BUFRMessage>` represent a single BUFR message. It primarily offers methods to:

 - :ref:`extract field metadata <metadata>`, such as :meth:`GribField.metadata() data.reader.bufr.bufr.BUFRMessage._metadata>`

Examples:

    - :ref:`/examples/grib_overview.ipynb`
    - :ref:`/examples/grib_metadata.ipynb`
    - :ref:`/examples/grib_selection.ipynb`
    - :ref:`/examples/grib_missing.ipynb`



to_pandas()
++++++++++++++

BUFR is a message based format and can contain both forecasts and observations. The structure of a BUFR message is typically hierarchical and can be rather complex, so the recommended way is to extract the required data with ``to_pandas()`` into a pandas DataFrame, which is much easier to work with. The BUFR data extraction in ``to_pandas()`` is implemented by :xref:`pdbufr`.

Examples:

    - :ref:`/examples/bufr.ipynb`
