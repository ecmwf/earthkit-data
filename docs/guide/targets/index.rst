.. _targets:

Targets
===============

A **target** can represent a file, a database, a remote server etc. Data is written/added to a target by using a suitable :ref:`encoder <encoders>`.

Details
----------------

.. toctree::
   :maxdepth: 1

   to_target
   target_objects


Examples
------------

  - :ref:`/examples/file_target.ipynb`
  - :ref:`/examples/grib_to_file_target.ipynb`
  - :ref:`/examples/grib_to_file_pattern_target.ipynb`
  - :ref:`/examples/grib_to_fdb_target.ipynb`
  - :ref:`/examples/grib_to_geotiff.ipynb`
  - :ref:`/examples/grib_to_zarr_target.ipynb`


Overview
----------------------------

There are different ways to write/add data to a given target:

  - using :func:`to_target` on a data object
  - using the standalone :func:`to_target` method
  - using a :py:class:`Target` object

.. code-block:: python

    import earthkit.data as ekd

    # read GRIB data into a fieldlist
    ds = ekd.from_source("file", "docs/examples/test.grib")

    # write the fieldlist to a file in different ways

    # Method 1: using to_target() on the data object
    ds.to_target("file", "_my_res_1.grib")

    # Method 2: using the standalone to_target() method
    ekd.to_target("file", "_my_res_2.grib", data=ds)

    # Method 3: using a target object
    with ekd.create_target("file", "_my_res_3.grib") as t:
        t.write(ds)

    # Method 4: using a target object
    from earthkit.data.targets.file import FileTarget

    with FileTarget("_my_res_4.grib") as t:
        t.write(ds)
