
.. _xr_grib_to_netcdf:


Converting GRIB to NetCDF
----------------------------

To convert GRIB data to NetCDF first we need to convert GRIB to Xarray with :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` then generate NetCDF from it with :py:meth:`xarray.Dataset.to_netcdf`. We have 3 options to do this:

Using the earthkit accessor
++++++++++++++++++++++++++++

By default, the earthkit Xarray engine attaches some special attributes to the generated Xarray dataset that cannot be written to NetCDF. In order to make ``to_netcdf()`` work we need to invoke it on the ``earthkit`` accessor and not directly on the Xarray dataset.

.. code-block:: python

    import earthkit.data as ekd

    ds_fl = ekd.from_source("sample", "pl.grib")
    ds_xr = ds_fl.to_xarray()
    ds_xr.earthkit.to_netcdf("_from_grib.nc")

Using the ``add_earthkit_attrs=False`` option
++++++++++++++++++++++++++++++++++++++++++++++++++

Alternatively, we can use the ``add_earthkit_attrs=False`` option in :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray`.  With this the earthkit attributes are not added to the generated dataset and it is safe to call :py:meth:`to_netcdf <xarray.Dataset.to_netcdf>` directly on it.

.. code-block:: python

    import earthkit.data as ekd

    ds_fl = ekd.from_source("sample", "pl.grib")
    ds_xr = ds_fl.to_xarray(add_earthkit_attrs=False)
    ds_xr.to_netcdf("_from_grib.nc")

Using to_target
++++++++++++++++

The third option is to use the :func:`to_target` method to convert GRIB directly to NetCDF. This method will generate an Xarray dataset and write it to a NetCDF file in one step.

.. code-block:: python

    import earthkit.data as ekd

    ds_fl = ekd.from_source("sample", "pl.grib")
    ds.fl.to_target("file", "_from_grib.nc")


To control the Xarray conversion we can pass options to the earthkit Xarray engine with ``earthkit_to_xarray_kwargs``. In this case ``add_earthkit_attrs=False`` is always enforced.

.. code-block:: python

    import earthkit.data as ekd

    ds_fl = ekd.from_source("sample", "pl.grib")
    ds.fl.to_target(
        "file", "_from_grib.nc", earthkit_to_xarray_kwargs={"flatten_values": True}
    )


Examples
++++++++++++

For further details see the following notebook:

- :ref:`/examples/grib_to_netcdf.ipynb`
