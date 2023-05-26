.. _bufr:


BUFR
---------

BUFR (Binary Universal Form for Representation of meteorological data) is a binary data format maintained by WMO. The earthkit-data interface supports both BUFR `edition 3 <https://community.wmo.int/en/activity-areas/wmo-codes/manual-codes/bufr-edition-3-and-crex-edition-1>`_ and `edition 4 <https://library.wmo.int/index.php?lvl=notice_display&id=10684>`_.

to_pandas()
++++++++++++++

BUFR is a message based format and can contain both forecasts and observations. The structure of a BUFR message is typically hierarchical and can be rather complex, so the recommended way is to extract the required data with ``to_pandas()`` into a pandas DataFrame, which is much easier to work with. The BUFR data extraction in ``to_pandas()`` is implemented by :xref:`pdbufr`.

Examples:

    - :ref:`/examples/bufr.ipynb`
