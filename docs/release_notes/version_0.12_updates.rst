Version 0.12 Updates
/////////////////////////


Version 0.12.5
===============

Fixed
++++++++

- Fixed issue when trying to iterate an empty source caused a crash (:pr:`630`)



Version 0.12.4
===============

Changes
++++++++

- made :py:class:`Field` available as a top level import

  .. code-block:: python

      from earthkit.data import Field


Version 0.12.3
===============

Changes
++++++++

- ``Field.resolution()`` now returns None when the resolution cannot be determined. Previously, it failed with an assertion (:pr:`616`)

Fixes
++++++++

- Fixed issue when there was a crash during checking missing MARS credentials when calling ``from_source("mars", ...)``. It only happened when ``ecmwfapi`` was used for MARS retrievals. (:pr:`615`)


Version 0.12.2
===============

Fixes
++++++++

- Fixed issue when failed to build a fieldlist with concatenation because maximum recursion depth exceeded (:pr:`599`)


Version 0.12.1
===============

Changes
++++++++

- Increased covjsonkit version to 0.1.1

Fixes
++++++++

- Fixed issue when the earthkit Xarray engine prevented opening geotiff with :py:meth:`xarray.open_dataset()` (:pr:`591`)
- Fixed issue when no "units" attribute was added to the Xarray dataset generated from a single GRIB variable (:pr:`592`)


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
