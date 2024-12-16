Version 0.12 Updates
/////////////////////////


Version 0.12.0
===============

Changes
++++++++

- Enabled using environment variables to control the :ref:`settings <settings>` (:pr:`565`). See the notebook example:

  - :ref:`/examples/settings_env_vars.ipynb`

- Re-enabled ``headers_only_clone=True`` when calling :meth:`GribMetadata.override() <data.readers.grib.metadata.GribMetadata.override>` (:pr:`567`)

- Added the :ref:`data-sources-ecfs` source to retrieve data from ECMWF's File Storage system (only available at ECMWF) (:pr:`568`)
- Made ``earthkit-geo`` an optional dependency (:pr:`569`) . See :ref:`install`.
- Enabled specifying the path to the standalone :ref:`MARS <data-sources-mars>`  client command via the ``MARS_CLIENT_EXECUTABLE`` environment variable (:pr:`566`)
- Add JAX array backend (:pr:`533`)
- Allow encoding of PL array for GribCoder (:pr:`546`)

Fixes
+++++

- Fixed issue when ``sel()`` failed on Xarray generated with the earthkit engine from a single GRIB field (:pr:`564`)
- Fixed issue when could not correctly update the :ref:`settings <settings>` config file from concurrent processes (:pr:`559`)
