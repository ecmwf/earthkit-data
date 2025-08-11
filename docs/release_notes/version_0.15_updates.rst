Version 0.15 Updates
/////////////////////////


Version 0.15.1
===============

Fixes
+++++++++++++++++

- Fixed issue when :func:`xarray.open_dataset` did not work with the "earthkit" engine when a ``pathlib.Path`` object specified the input data (:pr:`741`).


Version 0.15.0
===============

Deprecations
+++++++++++++++++++

- :ref:`deprecated-ens-dim-role`
- :ref:`deprecated-xarray-accessor-to-grib`

Xarray engine
++++++++++++++++++++++++++++++

Breaking xarray engine changes
-------------------------------

- Separated the dimension names from the metadata keys used to generate the dimensions. Dimensions associated with the dimension roles are now taking the name of the :ref:`dimension role <xr_dim_roles>`, irrespective of the metadata key the dimension role is mapped to. The example belows shows what this means for e.g. the "level" dimension role when the :ref:`mars profile <xr_profile_mars>`  (the default) is used. In this case the "level" role is mapped to the "levelist" ecCodes GRIB key.

    .. code-block:: python

        import earthkit.data as ekd

        ds_fl = ekd.from_source("sample", "pl.grib")
        ds_fl.to_xarray().coords


    With the new code the dimension/coordinate name will be "level". So the output is as follows::

        Coordinates:
        * forecast_reference_time  (forecast_reference_time) datetime64[ns] 32B 202...
        * step                     (step) timedelta64[ns] 16B 00:00:00 06:00:00
        * level                    (level) int64 16B 500 700
        * latitude                 (latitude) float64 152B 90.0 80.0 ... -80.0 -90.0
        * longitude                (longitude) float64 288B 0.0 10.0 ... 340.0 350.0


    However, using the previous version the output would be as follows::

        Coordinates:
        * forecast_reference_time  (forecast_reference_time) datetime64[ns] 32B 202...
        * step                     (step) timedelta64[ns] 16B 00:00:00 06:00:00
        * levelist                 (levelist) int64 16B 500 700
        * latitude                 (latitude) float64 152B 90.0 80.0 ... -80.0 -90.0
        * longitude                (longitude) float64 288B 0.0 10.0 ... 340.0 350.0


  The old behaviour can still be invoked by using the newly added ``dim_name_from_role_name=False`` option. See: :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray`.


- The ``step`` dimension role is now mapped to the ``step_timedelta`` metadata key, which is the ``datetime.timedelta`` representation of the ``"endStep"`` GRIB/metadata key. Previously, this role was mapped to the ``"step"`` key. This change was necessary for the following reasons:

  - allows handling cases when the ``step`` key contains ranges as a str in the form of e.g.  "12-24"
  - allows proper sorting of the "step" dimension values when building the dataset

 Please note that due to this change when ``dim_name_from_role_name=False`` is used the step dimension will be called "step_timedelta" instead of "step". You can still reproduce the old behaviour by using: ``dim_roles={"step": "step"}``. See the following notebook example: :ref:`/examples/xarray_engine_step_ranges.ipynb`.


Other Xarray engine changes
------------------------------

- Allowed using mappings in the ``extra_dims`` and ``fixed_dims`` options to define both the name of the dimensions and the metadata keys to generate their values. Previously, these options only took a single/multiple metadata keys. E.g. both the options below will generate the "expver", "mars_stream" and "mars_class" dimensions using the "expver", "stream" and "class" metadata keys.

   .. code-block:: python

       extra_dims = ["expver", {"mars_stream": "stream"}, ("mars_class", "class")]
       extra_dims = {
           "expver": "expver",
           "mars_stream": "stream",
           "mars_class": "class",
       }


- Improved the serialisation of GRIB fieldlists to reduce memory usage when Xarray is generated with chunks (:pr:`700`). See the :ref:`/examples/xarray_engine_chunks.ipynb` notebook example.
- TensorBackendArray, which implements the lazy loading of DataArrays in the Xarray engine, now uses a ``dask.utils.SerializableLock`` when accessing the data (:pr:`700`).
- Enabled converting :ref:`data-sources-lod` fieldlists into Xarray (:pr:`701`). See the :ref:`/examples/list_of_dicts_to_xarray.ipynb` notebook example.
- Enabled converting Xarray generated with the earthkit engine into GRIB using :func:`to_target` (:pr:`730`). See :ref:`xr_to_grib` and the related :ref:`/examples/xarray_engine_to_grib.ipynb` notebook example.

New Xarray engine notebooks
------------------------------

- :ref:`/examples/xarray_engine_step_ranges.ipynb`
- :ref:`/examples/xarray_engine_ensemble.ipynb`
- :ref:`/examples/xarray_engine_squeeze.ipynb`
- :ref:`/examples/xarray_engine_chunks.ipynb`
- :ref:`/examples/list_of_dicts_to_xarray.ipynb`



New features
+++++++++++++++++

- Added the :ref:`zarr <data-sources-zarr>` source to read Zarr data (:pr:`675`).
- Added the :ref:`targets-zarr` target (:pr:`716`). See the :ref:`/examples/grib_to_zarr_target.ipynb` notebook example.
- Added new config option ``grib-file-serialisation-policy`` to control how GRIB data on disk is pickled. The options are "path" and "memory". The default is "path". Previously, only "memory" was implemented (:pr:`700`).
- Added serialisation to GRIB fields (both on disk and in-memory) (:pr:`700`)
- Enabled specifying earthkit Xarray engine options via the ``earthkit_to_xarray_kwargs`` kwarg in :func:`to_target` when converting GRIB to NetCDF. See :ref:`xr_grib_to_netcdf` and related the :ref:`/examples/grib_to_netcdf.ipynb` notebook example. (:pr:`729`) E.g.

    .. code-block:: python

        ds.to_target(
            "netcdf", "pl.nc", earthkit_to_xarray_kwargs={"flatten_values": True}
        )



Fixes
+++++++++++++++++

- Fixed issue when the :ref:`data-sources-forcings` source  did not handle time-zone aware datetimes correctly (:pr:`693`).
