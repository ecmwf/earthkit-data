
.. _xr_to_grib:


Converting Xarray to GRIB
-------------------------

.. warning::

    This is an experimental feature and it is not yet fully supported.

By default, ``add_earthkit_attrs=True`` in :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` and some special earthkit attributes are added to the dataset. This is needed for the Xarray to GRIB conversion. For this reason, if the Xarray is modified we must ensure the variable attributes are copied to the new Xarray dataset. By default, variable attributes are not kept in Xarray computations so we need to set the global Xarray ``keep_attrs`` option to enable it. See the examples below for details.

.. note::

    When Xarray generated with ``time_dim_mode="valid_time"`` is converted to GRIB, the "stepRange"/"step" keys in all the resulting GRIB fields will be set to 0, regardless of wether the original GRIB data contained forecast or not.

Using to_target
++++++++++++++++

It is possible to directly write the Xarray dataset created with the earthkit engine into a GRIB file with :func:`to_target`. This is a memory efficient way to write GRIB to disk since only one field is loaded into memory at a time. We can call :func:`to_target` either on the ``earthkit`` accessor or as a top level function.

.. code-block:: python

    # ensure attributes are kept
    import xarray as xr

    xr.set_options(keep_attrs=True)

    # ds_xr is an Xarray dataset created with the earthkit engine, we modify it
    ds_xr += 1

    # option1: writing to GRIB file using the accessor
    ds_xr.earthkit.to_target("file", "_from_xr_1.grib")

    # option: 2writing to GRIB file using the top level function
    to_target("file", "_from_xr_2.grib", data=ds_xr)


Using to_fieldlist()
++++++++++++++++++++

We can also convert the Xarray dataset into a GRIB fieldlist by using :py:meth:`~data.utils.xarray.engine.XarrayEarthkit.to_fieldlist` on the ``earthkit`` accessor of the Xarray object. Please note that this will generate a fieldlist entirely stored in memory.

.. code-block:: python

    >>> import xarray as xr
    >>> xr.set_options(keep_attrs=True)
    >>> ds_xr += 1
    >>> ds_fl1 = ds_xr.earthkit.to_fieldlist()
    >>> ds_fl1[0]
    ArrayField(r,500,20240603,0,0,0)

The generated GRIB fieldlist can be saved to disk using the :func:`to_target` method.

.. code-block:: python

    ds_fl1.to_target("file", "_from_xr_3.grib")

Examples
++++++++++++

For further details see the following notebook:

- :ref:`/examples/xarray_engine_to_grib.ipynb`
