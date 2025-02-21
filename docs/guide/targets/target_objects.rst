.. _data-target-objects:

Target objects
===============

Each target is represented by a :py:class:`Target` object. The target object can be created using :func:`create_target` and then used to write data. For the list of built in targets see :ref:`built-in-targets`.

A :py:class:`Target` object has the following methods/properties:

.. list-table::
   :header-rows: 1

   * - Method/property
     - Description
   * - :py:meth:`~Target.write`
     - Write data to the target. Attempting to write to a closed target raises a ValueError.
   * - :py:meth:`~Target.close`
     - Close the target and release resources. Once closed, the target cannot be written to anymore. Attempting to call write, close or flush on a closed target raises a ValueError.
   * - :py:meth:`~Target.flush`
     - Flush the target. This method is optional and may not be implemented by all targets. Attempting to flush to a closed target raises a ValueError.
   * - :py:attr:`~Target.closed`
     - True if the target is closed, False otherwise.

Usage
----------------------

This example writes a FieldList to a target.

.. code-block:: python

    import earthkit.data as ekd

    # read GRIB data into a fieldlist
    ds = ekd.from_source("file", "docs/examples/test.grib")

    # writing in a loop field by field
    t = ekd.create_target("file", "_my_res.grib")
    for f in ds:
        t.write(f)
    t.close()

    # t cannot be written to anymore

    # writing in one go
    t = ekd.create_target("file", "_my_res_1.grib")
    t.write(ds)
    t.close()

    # t cannot be written to anymore


Target objects can also be used a context manager. When used as a context manager, the target is automatically closed when the context is exited.

.. code-block:: python

    import earthkit.data as ekd

    # read GRIB data into a fieldlist
    ds = ekd.from_source("file", "docs/examples/test.grib")

    with ekd.create_target("file", "_my_res.grib") as t:
        for f in ds:
            t.write(f)



create_target()
---------------------------

Create a new target :py:class:`Target` object.


.. py:function:: create_target(name, *args, **kwargs)

  Create a new target :py:class:`Target` object.

  :param str name: the target (see :ref:`built-in-targets`)
  :param tuple *args: specify target parameters
  :param dict **kwargs: specify additional target parameters. Also specify the encoder parameters.
