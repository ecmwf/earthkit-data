Version 0.17 Updates
/////////////////////////


Version 0.17.0
===============

New features
++++++++++++++++++++++++++++++

- Implemented the ``allow_holes`` option in the Xarray engine to allow using GRIB input not forming a complete hypercube (:pr:`780`). The default is ``allow_holes=False``. See the notebook example:

    - :ref:`/examples/xarray_engine_holes.ipynb`

- Added the experimental :ref:`data-sources-gribjump` source for fast retrievals of GRIB message subsets from the FDB (Fields DataBase) using the :xref:`gribjump` library (:pr:`689`). See the notebook example:

    - :ref:`/examples/gribjump.ipynb`

- Added the :func:`to_geojson` method to CovjsonReader for conversion to geojson from covjson (:pr:`794`). Requires ``covjsonkit>=0.2.2``.
- Allowed reading multiple GRIB messages from a memory buffer with the :ref:`data-sources-memory` source (:pr:`740`).


Fixes
++++++++

- Fixed prompt error in the :ref:`data-sources-mars` source (:pr:`767`)
- Fixed issue when wrong environment variable names were used in the :ref:`config` examples (:pr:`768`)
- Fixed missing coordinate attributes in generated Xarray datasets (:pr:`785`)
- Fixed issue when Xarray built from GRIB data containing temporal accumulation was not correctly written to GRIB  (:pr:`799`)
- Fixed handling empty slices in datasets/dataarrays generated with the Xarray engine (:pr:`802`)
- Fixed issue when could not convert FDB data retrieved lazily to Xarray due to missing step information (:pr:`815`)
- Replaced the usage of ``functools.cached_property`` with a custom thread safe implementation. This was needed because ``functools.cached_property`` is not thread safe as of Python 3.12 (:pr:`814`, :pr:`817`).
