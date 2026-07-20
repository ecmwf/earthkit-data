.. _release-notes-1.1:

Version 1.1 Updates
///////////////////////


Version 1.1.0
==============

Deprecations
+++++++++++++++++++

- :ref:`deprecated-levtype-grib-encoder`


Changes
++++++++++++

- The ``level`` ecCodes key is no longer silently renamed to ``levelist`` by
  :py:meth:`earthkit.data.encoders.GribEncoder.encode`. It is now written to the GRIB
  message unchanged.


Fixes
+++++++++++++

- Fixed issue when could not convert multiple NetCDF files to Xarray or fieldlist (:pr:`1074`). This happened when the source contained multiple directories or archives (e.g. tar) each containing multiple NetCDF files. It also happened when data was retrieved from a remote source (e.g. "cds") and the source contained multiple archive files each with multiple NetCDF files.
- Fixed issue when could not convert multiple CSV files to a pandas dataframe (:pr:`1075`).
- Fixed issue when calling `MultiData.available_types` raised an exception (:pr:`1075`).
- Fixed issue when setting the ``level`` key without specifying the level type in :py:meth:`earthkit.data.encoders.GribEncoder.encode` resulted in incorrect GRIB messages always containing ``typeOfLevel=isobaricInhPa`` irrespective of the original/template data (:pr:`1077`).
