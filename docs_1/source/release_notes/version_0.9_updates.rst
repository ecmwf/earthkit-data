Version 0.9 Updates
/////////////////////////

Version 0.9.4
===============

Changes
+++++++

- Increased the minimum version of the `cdsapi` package to 0.7.1.

Version 0.9.3
===============

Fixes
++++++

- When "expect=any" is used in a request for the :ref:`data-sources-mars` source and no data is available :func:`from_source` now returns an empty fieldlist. Previously an exception was thrown.


Version 0.9.2
===============

Fixes
++++++

- When "shortName" is "~" in the GRIB header, :func:`metadata` now returns the value of "paramId" as a str for both the "param" and "shortName" keys. Previously "~" was returned for both these keys.


Version 0.9.0
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
