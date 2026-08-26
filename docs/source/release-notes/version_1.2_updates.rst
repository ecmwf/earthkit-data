.. _release-notes-1.2:

Version 1.2 Updates
///////////////////////



Version 1.2.2
==============

Fixes
++++++++++++

- Fixed issue when the :ref:`data-sources-ecfs` source could not retrieve tar files  (:pr:`1122`)


Version 1.2.1
==============

Fixes
++++++++++++

- Fixed issue when NetCDF data downloaded from a CORDEX dataset in the :ref:`data-sources-cds` source could not be converted to a fieldlist (:pr:`1114`)
- Fixed issue when fields created from Xarray or NetCDF data did not show the geography component in ``describe()`` (:pr:`1116`)
- Fixed issue when ``geography.grid_type`` was always ``None`` for fields created from Xarray or NetCDF data (:pr:`1116`)


Version 1.2.0
==============

Deprecations
+++++++++++++++++++

- :ref:`deprecated-wekeocds` (:pr:`1091`, :pr:`1102`, :pr:`1104`)
- :ref:`deprecated-fdb-userconfig` (:pr:`1091`, :pr:`1102`, :pr:`1104`)


New Features
++++++++++++

- Added the ``path`` property to data objects (:pr:`1085`, :pr:`1069`)
- Added lunar distance calculations to the :ref:`data-sources-forcings` source (:pr:`1059`)
- Allowed using earthkit-meteo solar and lunar methods in the :ref:`data-sources-forcings` source. When earthkit-meteo is installed its methods are used in the computations, otherwise the equivalent local code from earthkit-data is used (:pr:`1090`, :pr:`1101`)

Changes
++++++++++++

- Implemented consistent exception handling in `LazyFieldComponentHandler` and `LazySource` (:pr:`1071`)
- Changed the Field `parameter.standard_name` to use None instead of "unknown" when loaded from GRIB data (:pr:`1086`)
- Altered the Xarray engine to avoid using ecCodes GRIB keys unnecessarily (:pr:`1092`)


Fixes
++++++++++++

* Fixed using custom options for pytest (:pr:`1058`)
* Fixed docstrings quotes around parameter.variable (:pr:`1066`)
* Fixed the Xarray engine default profile to enable using ``add_valid_time_coord=True`` with GRIB data containing a single valid time (:pr:`1072`)
* Fixed the Field proc component's GRIB context collector (:pr:`1088`)
* Made ``create_fieldlist()`` work with iterables (:pr:`1089`)
