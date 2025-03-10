.. _parts:

Using parts for file, s3 and url sources
==========================================

For the :ref:`data-sources-file`, :ref:`data-sources-s3` and :ref:`data-sources-url` sources we can specify the parts (byte ranges) we want to read from the given input.

A **single part** is a pair (list or tuple) in the following format::

    (offset, length)

where:

    - offset: the start byte position
    - length: the number of bytes to be read from the offset

**Multiple parts** can be defined as a list or tuple of single parts. These have to be specified in an ascending offset order, no overlapping is allowed.


Using the parts kwarg
----------------------

.. note::

    The ``parts`` kwarg only works for the :ref:`data-sources-file` and :ref:`data-sources-url` sources.


For both sources we can use the ``parts`` kwarg to define the parts for all the ``path``\s or ``urls``\ s. A few examples:

.. code-block:: python

    import earthkit.data as ekd

    # file
    ds = ekd.from_source("file", "my.grib", parts=(0, 150))
    ds = ekd.from_source("file", "my.grib", parts=[(0, 150), (400, 160)])

    # url
    ds = ekd.from_source("url", "http://my-host/my.grib", parts=(0, 150))
    ds = ekd.from_source("url", "http://my-host/my.grib", parts=[(0, 150), (400, 160)])


Specifying the parts for each file
-------------------------------------

.. note::

    The technique described below only works for the :ref:`data-sources-file` and :ref:`data-sources-url` sources.


If we have multiple paths/urls and want to specify different parts for each we need to add the parts to the  ``path`` or ``urls`` arguments.

.. code-block:: python

    import earthkit.data as ekd

    # file
    ds = ekd.from_source(
        "file",
        [
            ("a.grib", (0, 150)),
            ("b.grib", (240, 120)),
            ("c.grib", None),
            ("d.grib", [(240, 120), (720, 120)]),
        ],
    )

When we use this mode the ``parts`` kwarg cannot be used!

Examples:

    - :ref:`/examples/file_parts.ipynb`


Specifying the parts for S3
---------------------------

For the :ref:`data-sources-s3` source the parts have to be specified within the request.

Examples:

    - :ref:`/examples/s3.ipynb`
