Deprecations
=============

Version 0.13.0
-----------------

.. _deprecated-data-save:

:func:`save` is deprecated on data objects
++++++++++++++++++++++++++++++++++++++++++++

Use the :ref:`targets <data-targets>` instead.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -
       .. code-block:: python

           import earthkit.data as ekd

           ds = ekd.from_source("sample", "test.grib")

           ds.save("res.grib")
           ds.save("res1.grib", append=True)
           ds.save("res.grib", bits_per_value=12)

           for field in ds:
               field.save("res2.grib", append=True, bits_per_value=12)
   * - New code
   * -
       .. code-block:: python

           import earthkit.data as ekd

           ds = ekd.from_source("sample", "test.grib")

           ds.to_target("file", "res.grib")
           ds.to_target("file", "res1.grib", append=True)
           ds.to_target("file", "res.grib", metadata={"bitsPerValue": 12})

           with create_target("file", "res2.grib", metadata={"bitsPerValue": 12}) as t:
               for field in ds:
                   t.write(field)

           with create_target("file", "res2.grib") as t:
               for field in ds:
                   t.write(field, metadata={"bitsPerValue": 12})

           with create_target("file", "res2.grib") as t:
               for field in ds:
                   t.write(field, bitsPerValue=12)


.. _deprecated-data-write:

:func:`write` is deprecated on data objects
++++++++++++++++++++++++++++++++++++++++++++

Use the :ref:`targets <data-targets>` instead.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -
       .. code-block:: python

           import earthkit.data as ekd

           ds = ekd.from_source("sample", "test.grib")

           with open("res.grib", "wb") as f:
               ds.write(f)

           with open("res.grib", "wb") as f:
               for field in ds:
                   field.write(f)

   * - New code
   * -
       .. code-block:: python

           import earthkit.data as ekd

           ds = ekd.from_source("sample", "test.grib")

           with open("res.grib", "wb") as f:
               ds.to_target("file", f)

           with open("res.grib", "wb") as f:
               for field in ds:
                   field.to_target("file", f)

           with open("res.grib", "wb") as f:
               t = create_target("file", f)
               t.write(ds)

           with open("res.grib", "wb") as f:
               t = create_target("file", f)
               for field in ds:
                   t.write(field)


.. _deprecated-new-grib-output:

:func:`new_grib_output` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

:func:`new_grib_output` returns a new :py:class:`GribOutput` object. Use the :ref:`targets <data-targets>` instead.

.. warning::

    When using :func:`new_grib_output` if the specified metadata does not contain the ``generatingProcessIdentifier`` key is automatically set to ``255``. The new API does not have this behavior.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -
       .. code-block:: python

           import earthkit.data as ekd

           ds = ekd.from_source("sample", "test.grib")

           o = ekd.new_grib_output("res.grib")
           for field in ds:
               o.write(shortName="2t", template=field)
           o.close()

           with ekd.new_grib_output("res1.grib") as o:
               for field in ds:
                   o.write(shortName="2t", template=field)

   * - New code
   * -
       .. code-block:: python

           import earthkit.data as ekd

           ds = ekd.from_source("sample", "test.grib")

           t = create_target(
               "file",
               "res.grib",
               metadata={"shortName": "2t", "generatingProcessIdentifier": 255},
           )
           for field in ds:
               t.write(field)
           o.close()

           t = create_target("file", "res.grib")
           for field in ds:
               t.write(data=field, shortName="2t", generatingProcessIdentifier=255)
           o.close()

           t = create_target("file", "res.grib")
           for field in ds:
               t.write(shortName="2t", template=field, generatingProcessIdentifier=255)
           t.close()

           with create_target("file", "res.grib") as t:
               for field in ds:
                   t.write(field, shortName="2t", generatingProcessIdentifier=255)

.. _deprecated-griboutput:

:py:class:`GribOutput` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

Use the :ref:`targets <data-targets>` instead. For details see :ref:`migrating new_grib_output() <deprecated-new-grib-output>`.


.. _deprecated-new-grib-coder:

:func:`new_grib_coder` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

:func:`new_grib_coder` returns a new :py:class:`GribCoder` object. Use the :ref:`targets <data-targets>` instead.

.. warning::

    When using :func:`new_grib_coder` if the specified metadata does not contain the ``generatingProcessIdentifier`` key is automatically set to ``255``. The new API does not have this behavior.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -
       .. code-block:: python

           import earthkit.data as ekd

           ds = ekd.from_source("sample", "test.grib")

           values = ds[1].values + 1

           from earthkit.data.readers.grib.output import new_grib_coder

           c = new_grib_coder()
           # is a GribCodesHandle
           d = c.encode(values, shortName="2t", template=ds[1])

           c = new_grib_coder(template=ds[1])
           # is a GribCodesHandle
           d = c.encode(values, shortName="2t")

   * - New code
   * -
       .. code-block:: python

           import earthkit.data as ekd

           ds = ekd.from_source("sample", "test.grib")

           values = ds[1].values + 1

           c = ekd.create_encoder("grib")
           d = c.encode(
               values=values,
               template=ds[1],
               shortName="2t",
               generatingProcessIdentifier=255,
           )
           # d is a GribEncodedData

           c = ekd.create_encoder("grib")
           d = c.encode(
               ds[1], values=values, shortName="2t", generatingProcessIdentifier=255
           )

           c = ekd.create_encoder(
               "grib", template=ds[1], generatingProcessIdentifier=255
           )
           d = c.encode(
               values=values,
               shortName="2t",
           )


.. _deprecated-gribcoder:

:py:class:`GribCoder` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

Use the :ref:`encoders <data-encoders>` instead. For details see :ref:`migrating new_grib_coder() <deprecated-new-grib-coder>`.
