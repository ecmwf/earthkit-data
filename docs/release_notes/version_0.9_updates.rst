Version 0.9 Updates
/////////////////////////

Version 0.9.1
===============

New features
++++++++++++++++

- Renamed the ``constants`` source to ``forcings``
- Enabled the NetCDF field parser to recognise the following additional coordinates:  "X", "xc", "Y" and "yc"
- Split encoding from writing in experimental GRIB output generator

Fixes
++++++

- Fixed issue when NetCDF data containing cftime dates could not be read
- Fixed issue when NetCDF data containing coordinates called "lat" and "lon" could not be read correctly
