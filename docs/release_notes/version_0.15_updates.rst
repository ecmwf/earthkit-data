Version 0.15 Updates
/////////////////////////


Version 0.15.0
===============

Deprecations
+++++++++++++++++++

- :ref:`deprecated-ens-role`

Xarray engine
++++++++++++++++++++++++++++++

Breaking changes
-------------------

- Separated the dimension names from the metadata keys used to generate the dimensions. Dimensions associated with the dimension roles are now taking the name of the dimension role, irrespective of the metadata key the dimension role is mapped to. E.g.: the "level_type" dimension role now generates a dimension called "level_type". Previously, the dimension name was the name of the associated metadata key: e.g. it was "levtype" in the :ref:`default <xr_profile_mars>` profile. The old behaviour can still be invoked by using the newly added ``keep_dim_role_names=False`` option.

.. list-table:: Dimension roles and their associated metadata keys
   :header-rows: 1

   * - Dimension role
     - Pow
     - Previously
   * - Dimension role"
     - "level_type"
     - "level_type"
   * - "Dimension name"
     - "stream"
   * - "mars_class"
     - "class"
   * - "mars_typeOfLevel"
     - "typeOfLevel"
   * - "mars_level_type"
     - "levtype"
   * - "mars_step_timedelta"
     - "endStep"
   * - "mars_step"


- The ``step`` dimension role is now mapped to the ``step_timedelta`` metadata key, which is the ``datatime.timedelta`` representation of the ``"endStep"`` GRIB/metadata key. Previously, this role was mapped to the ``"step"`` key. Please note that due to this change when ``keep_dim_role_names=False`` is used the step dimension will be called "step_timedelta" instead of "step".


Other changes
-------------------

- Allowed using mappings in the ``ensure_dims``, ``extra_dims`` and ``fixed_dims`` options to define both the name of the dimensions and the metadata keys to generate their values. Previously, these options only took a single/multiple metadata keys. E.g. both the options below will generate the "expver", "mars_stream" and "mars_class" dimensions using the "expver", "stream" and "class" metadata keys.

   .. code-block:: python

       extra_dims = ["expver", {"mars_stream": "stream"}, ("mars_class", "endStep")]
       extra_dims = {
           "expver": "expver",
           "mars_stream": "stream",
           "mars_class": "endStep",
       }


- Improved the serialisation of GRIB fieldlists to reduce memory usage when Xarray is generated with chunks (:pr:`700`). See the :ref:`/examples/xarray_engine_chunks.ipynb` notebook example.
- TensorBackendArray, which implements the lazy loading of DataArrays in the Xarray engine, now uses a ``dask.utils.SerializableLock`` when accessing the data (:pr:`700`).
- Enabled converting :ref:`data-sources-lod` fieldlists into Xarray (:pr:`701`). See the :ref:`/examples/list_of_dicts_to_xarray.ipynb` notebook example.


New features
+++++++++++++++++

- Added new config option ``grib-file-serialisation-policy`` to control how GRIB data on disk is pickled. The options are "path" and "memory". The default is "path". Previously, only "memory" was implemented (:pr:`700`).
- Added serialisation to GRIB fields (both on disk and in-memory) (:pr:`700`)


Fixes
+++++++++++++++++

- Fixed issue when the :ref:`data-sources-forcings` source  did not handle time-zone aware datetimes correctly (:pr:`693`).
