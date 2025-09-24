Version 0.17 Updates
/////////////////////////


Version 0.17.0
===============

New features
++++++++++++++++++++++++++++++

- Implemented the ``allow_holes`` option in the Xarray engine to allow using GRIB input not forming a complete hypercube (:pr:`734`)
- Added the experimental :ref:`data-sources-gribjump` source for fast retrievals of GRIB message subsets from the FDB (Fields DataBase) using the :xref:`gribjump` library. See the notebook example:

    - :ref:`/examples/gribjump.ipynb`

- Added the :func:`to_geojson` method to CovjsonReader for conversion to geojson from covjson (:pr:`794`). Requires ``covjsonkit>=0.2.2``.

Fixes
++++++++

- Fixed prompt error in the :ref:`data-sources-mars` source (:pr:`767`)
- Fixed issue when wrong environment variable names were used in the :ref:`config` examples (:pr:`768`)
- Fixed missing coordinate attributes in generated Xarray datasets (:pr:`785`)
- Fixed issue when Xarray built from GRIB data containing temporal accumulation was not correctly written to GRIB  (:pr:`799`)
- Fixed handling empty slices in datasets/dataarrays generated with the Xarray engine (:pr:`802`)
