.. _xr_engine:

Xarray engine: overview
////////////////////////

Earthkit-data comes with its own Xarray engine called "earthkit" to perform conversions between :ref:`grib` and Xarray data.

Creating Xarray from GRIB
--------------------------

Using to_xarray()
++++++++++++++++++

We can convert :ref:`grib` data into an Xarray dataset by using :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` on a GRIB fieldlist object.

.. code-block:: python

    >>> import earthkit.data as ekd
    >>> ds_fl = ekd.from_source("sample", "pl.grib")
    >>> ds_xr = ds_fl.to_xarray()
    >>> ds_xr
    <xarray.Dataset> Size: 176kB
    Dimensions:  (forecast_reference_time: 4, step: 2, levelist: 2,
                  latitude: 19, longitude: 36)
    Coordinates:
        * forecast_reference_time  (forecast_reference_time) datetime64[ns] 32B 202...
        * step                     (step) timedelta64[ns] 16B 00:00:00 06:00:00
        * level                    (level) int64 16B 500 700
        * latitude                 (latitude) float64 152B 90.0 80.0 ... -80.0 -90.0
        * longitude                (longitude) float64 288B 0.0 10.0 ... 340.0 350.0
    Data variables:
        r                        (forecast_reference_time, step, level, latitude, longitude) float64 88kB ...
        t                        (forecast_reference_time, step, level, latitude, longitude) float64 88kB ...
     ...

.. note::

    By default, :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` uses the "earthkit" engine to generate Xarray. The previously used :xref:`cfgrib` engine is still available and can be invoked with the ``engine="cfgrib"`` option.


Using open_dataset()
++++++++++++++++++++

We can also use the Xarray engine to read GRIB data directly with the :py:func:`xarray.open_dataset` function. Naturally, this feature requires earthkit-data to be installed.

.. code-block:: python

    >>> import xarray as xr
    >>> ds_xr = xr.open_dataset("pl.grib", engine="earthkit")
    >>> ds_xr
    <xarray.Dataset> Size: 176kB
    ...

Dimensions
++++++++++

The pivotal question when generating the Xarray dataset is how to form the dimensions. The :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` method has a number of options to control the dimensions. Please see more details in the :ref:`dimensions <xr_dim>` section.


Profiles
+++++++++

:py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` has a large number of keyword arguments to control how the Xarray dataset is generated. To simplify the usage we can define :ref:`profiles <xr_profile>` providing custom defaults for most of the keyword arguments. For more details see :ref:`xr_profile`.


Examples
+++++++++

The following notebooks give details about how :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` can be used:

- :ref:`Xarray engine examples <examples_xr_engine>`


.. _xr_to_grib:


Converting Xarray to GRIB
-------------------------

.. warning::

    This is an experimental feature and it is not yet fully supported.

By default, ``add_earthkit_attrs=True`` in :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` and some special earthkit attributes are added to the dataset. This is needed for the Xarray to GRIB conversion. For this reason, if the Xarray is modified we must ensure the variable attributes are copied to the new Xarray dataset. By default, variable attributes are not kept in Xarray computations so we need to set the global Xarray ``keep_attrs`` option to enable it.See the examples below for details.

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

For further details see the following notebook:

- :ref:`/examples/xarray_engine_to_grib.ipynb`


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
    ds_fl.to_target("file", "_from_grib.nc")


To control the Xarray conversion we can pass options to the earthkit Xarray engine with ``earthkit_to_xarray_kwargs``. In this case ``add_earthkit_attrs=False`` is always enforced.

.. code-block:: python

    import earthkit.data as ekd

    ds_fl = ekd.from_source("sample", "pl.grib")
    ds_fl.to_target(
        "file", "_from_grib.nc", earthkit_to_xarray_kwargs={"flatten_values": True}
    )


For further details see the following notebook:

- :ref:`/examples/grib_to_netcdf.ipynb`
