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
        * levelist                 (levelist) int64 16B 500 700
        * latitude                 (latitude) float64 152B 90.0 80.0 ... -80.0 -90.0
        * longitude                (longitude) float64 288B 0.0 10.0 ... 340.0 350.0
    Data variables:
        r                        (forecast_reference_time, step, levelist, latitude, longitude) float64 88kB ...
        t                        (forecast_reference_time, step, levelist, latitude, longitude) float64 88kB ...
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


Profiles
+++++++++

:py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` has a large number of keyword arguments to control how the Xarray dataset is generated. To simplify the usage we can define :ref:`profiles <xr_profile>` providing custom defaults for most of the keyword arguments. For more details see :ref:`xr_profile`.


Examples
+++++++++

The following notebooks give details about how :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` can be used:

- :ref:`Xarray engine examples <examples_xr_engine>`


Converting Xarray to GRIB
-------------------------

.. warning::

    This is an experimental feature and it is not yet fully supported.

Xarray datasets created with the earthkit engine can be converted back to GRIB format by using :py:meth:`~data.utils.xarray.engine.XarrayEarthkit.to_fieldlist` on the ``earthkit`` accessor of the Xarray object. If the original Xarray was modified we must ensure the variable attributes are copied to the new Xarray dataset. By default, variable attributes are not kept in Xarray computations so we need to set the global Xarray ``keep_attrs`` option to enable it.

.. code-block:: python

    >>> import xarray as xr
    >>> xr.set_options(keep_attrs=True)
    >>> ds_xr += 1
    >>> ds_fl1 = ds_xr.earthkit.to_fieldlist()
    >>> ds_fl1[0]
    ArrayField(r,500,20240603,0,0,0)

The generated GRIB fieldlist can be saved to disk using the :py:meth:`~data.readers.grib.index.GribFieldList.save` method.

.. code-block:: python

    ds_fl1.save("_from_xr_1.grib")


It is also possible to directly write the Xarray into a GRIB file when calling :py:meth:`~data.utils.xarray.engine.XarrayEarthkit.to_grib` on the ``earthkit`` accessor. This will be a more memory efficient way to write GRIB to disk than generating a fieldlist first.

.. code-block:: python

    ds_xr.earthkit.to_grib("_from_xr_2.grib")

For further details see the following notebook:

- :ref:`/examples/xarray_engine_to_grib.ipynb`


Converting GRIB to NetCDF
----------------------------

To convert GRIB data to NetCDF first we need to convert GRIB to Xarray with :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` then generate NetCDF from it with :py:meth:`xarray.Dataset.to_netcdf`. Earthkit-data attaches some special attributes to the generated Xarray dataset that we do not want to write to NetCDF. In order to achieve this we need to call :py:meth:`xarray.Dataset.to_netcdf` on the ``earthkit`` accessor and not directly on the Xarray dataset.

.. code-block:: python

    ds_xr.earthkit.to_netcdf("_from_grib.nc")

For further details see the following notebook:

- :ref:`/examples/grib_to_netcdf.ipynb`
