Version 1.0.0 Release Candidate Updates
///////////////////////////////////////


Version 1.0.0rc2
==================

Changes
-------

- Changed the default value for the Field ``ensemble.member`` metadata from "0" to None. It is used when the Field does not contain any ensemble member information. (:pr:`960`).

Fixes
-------

- Fixed issue when the geography for GRIB data on ORCA and ICON grids was not correctly handled (:pr:`961`).



Version 1.0.0rc0
==================

This version is a release candidate for the upcoming 1.0.0 release. It includes a very large number of changes, including new and removed features. Please see the :ref:`migration_1.0.0` for more details on the changes and how to update your code to be compatible with 1.0.0.
