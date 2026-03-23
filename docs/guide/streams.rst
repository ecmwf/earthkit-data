.. _streams:

Streams
==========

We can read :ref:`grib` and CoverageJson data as a stream by using the ``stream=True`` option in :func:`from_source`. It is only available for the following sources:

- :ref:`data-sources-file`
- :ref:`data-sources-url`
- :ref:`data-sources-fdb`
- :ref:`data-sources-polytope`
- :ref:`data-sources-s3`

Iterating over a stream
------------------------

When reading a stream we need to call :meth:`to_fieldlist` on the returned object to get an iterable of Fields. Once the iteration is finished the stream data is not available any longer.

The example below shows how we iterate through a GRIB data stream field by field:

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> url = "https://sites.ecmwf.int/repository/earthkit-data/examples/test6.grib"
    >>> fl = ekd.from_source("url", url, stream=True).to_fieldlist()
    >>> for f in fl:
    ...     print(f)
    ...
    GribField(t,1000,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)
    GribField(u,850,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)

We can also use :meth:`~data.core.fieldlist.FieldList.batched` to iterate in batches of fixed size. Each iteration step now yields a :class:`Fieldlist`.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> url = "https://sites.ecmwf.int/repository/earthkit-data/examples/test6.grib"
    >>> fl = ekd.from_source("url", url, stream=True).to_fieldlist()
    >>> for f in fl.batched(2):
    ...     print(f"len={len(f)} {f.get(('parameter.variable', 'vertical.level'))}")
    ...
    len=2 [('t', 1000), ('u', 1000)]
    len=2 [('v', 1000), ('t', 850)]
    len=2 [('u', 850), ('v', 850)]

Another option is to use :meth:`~data.core.fieldlist.FieldList.group_by` to iterate in groups defined by metadata keys. Each iteration step results in a :class:`Fieldlist`, which is built by consuming GRIB messages from the stream until the values of the metadata keys change.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> url = "https://sites.ecmwf.int/repository/earthkit-data/examples/test6.grib"
    >>> fl = ekd.from_source("url", url, stream=True).to_fieldlist()
    >>> for f in fl.group_by("vertical.level"):
    ...     print(f"len={len(f)} {f.get(('parameter.variable', 'vertical.level'))}")
    ...
    len=3 [('t', 1000), ('u', 1000), ('v', 1000)]
    len=3 [('t', 850), ('u', 850), ('v', 850)]


Reading all the data into memory
----------------------------------

We can load the whole stream into memory by using  ``read_all=True`` in :meth:`to_fieldlist`. The resulting object will be a :py:class:`FieldList` storing all the Fields in memory. **Use this option carefully!**

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> url = "https://sites.ecmwf.int/repository/earthkit-data/examples/test6.grib"
    >>> fl = ekd.from_source("url", url, stream=True).to_fieldlist(read_all=True)
    >>> len(fl)
    6

Further examples
-----------------

- :ref:`/examples/source/data_from_stream.ipynb`
- :ref:`/examples/source/file_stream.ipynb`
- :ref:`/examples/source/fdb.ipynb`
- :ref:`/examples/source/url_stream.ipynb`
