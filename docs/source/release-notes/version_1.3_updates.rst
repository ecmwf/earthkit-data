.. _release-notes-1.3:

Version 1.3 Updates
///////////////////////

Version 1.3.1
==============

Fixes
++++++++++++

- Fixed issue when the model and source were not included in the cache key in the :ref:`data-sources-eod` source (:pr:`1203`)
- Fixed issue when building a field from GRIB data generated unwanted logs for unstructured grids with zero uid (:pr:`1211`)


Version 1.3.0
==============

New Features
++++++++++++

- Added the :ref:`data-sources-sql` source for SQL databases and also enabled the :ref:`data-sources-file` source to read SQL files (:pr:`810`). See the examples:

   - :ref:`/tutorials/source/sql_source.ipynb`
   - :ref:`/tutorials/sql/sql.ipynb`

- Added support for the ``pcraster`` data type (:pr:`1143`). See the example:

   - :ref:`/tutorials/pcraster/pcraster.ipynb`

- Added support for reading BUFR data from a :ref:`data-sources-stream` or from :ref:`data-sources-memory` (:pr:`1186`). See the examples:

   -  :ref:`/tutorials/bufr/bufr_file_stream.ipynb`
   -  :ref:`/how-tos/read_bufr_message_from_memory.ipynb`

- Refactored the internal handling of multi-file/multi-source data (:pr:`1133`) including:

    - New ``merger=False`` value, accepted by the :ref:`data-sources-file`, :ref:`data-sources-url`, and :ref:`data-sources-multi` sources, disables merging entirely and returns a ``MultiData`` object exposing each input individually (e.g. via .path).
    - Reworked earthkit.data.mergers (fieldlist, pandas, xarray) to support the new ``merger=False`` path alongside the existing merging behaviour.
    - Enabled concatenation for data loaded via :ref:`from_object`.
    - Added documentation for concatenation and merging. See:

        - :ref:`/concepts/concat.rst`
        - :ref:`/concepts/misc/mergers.rst`

    Also see the following example:

        :ref:`/how-tos/read_file_list.ipynb`

- Added a ``split`` option to the :ref:`data-sources-url` source. When ``True`` and multiple URLs are given, each URL is downloaded into its own separate target file instead of being concatenated into a single file (:pr:`1191`)
- Added a ``session`` kwarg to the :ref:`data-sources-url` source to allow passing in a custom ``requests`` session (:pr:`1131`)
- Added a config option ``url-maximum-retries`` (default 5) and ``url-retry-after`` (default 10s), controlling the number of retries for URL downloads (:pr:`1150`)
- Added support for converting polytope CoverageJSON data into a fieldlist (:pr:`1120`)
- Added ``to_fieldlist`` to the CoverageJSON data object (:pr:`1121`)
- Added an empty data object (:pr:`1132`)

Changes
++++++++++++

- Allowed using the ``parameter.units`` metadata key when selecting on a fieldlist with ``sel`` (:pr:`1188`)
- Allowed using relative date strings (e.g. ``"-1"``) in MARS requests (:pr:`1187`)
- The ``standard_name`` "forecast_reference_time" is now recognised as the time dimension when building a fieldlist from Xarray data (:pr:`1173`)
- Improved encoding of fields on unstructured grids into GRIB (:pr:`1166`)
- Improved support for GRIB data on unstructured grids (:pr:`1159`)
- Simplified and consolidated the internal reader implementations (:pr:`1127`)
- Raise an error when invalid keyword arguments are passed to ``from_source`` or to the underlying readers (:pr:`1112`)
- Omitted variables referenced via the ``coordinates``, ``bounds``, ``grid_mapping`` and ``climatology`` attributes of data/coordinate variables when loading Xarray/NetCDF data (:pr:`1126`)

Fixes
++++++++++++

- Fixed a state key mismatch that could cause errors when pickling a field's vertical component (:pr:`1176`)
- Fixed sub-hourly time handling in ``cos_solar_zenith_angle`` (:pr:`1172`)
- Added missing ``__repr__`` and ``_repr_html_`` methods to data objects (:pr:`1161`)
- Fixed detection of PP files based on their magic bytes (:pr:`1158`)
- Fixed detection of tar archives to rely on file contents rather than the file extension (:pr:`1141`)
- Fixed the NumPy reader (:pr:`1144`)
- Fixed passing kwargs through the zip, tar and archive readers (:pr:`1138`)
- Fixed docstrings for zarr data (:pr:`1162`)


Dependencies
++++++++++++

Added new optional dependency for SQL support:

    .. code-block:: ini

        optional-dependencies.sql = ["sqlalchemy>=2"]


New tutorials
++++++++++++++++++++++++++++

- :ref:`/tutorials/source/sql_source.ipynb`
- :ref:`/tutorials/sql/sql.ipynb`
- :ref:`/tutorials/pcraster/pcraster.ipynb`
- :ref:`/tutorials/bufr/bufr_file_stream.ipynb`


New how-tos
++++++++++++++++++++++++++++

- :ref:`/how-tos/read_bufr_message_from_memory.ipynb`
- :ref:`/how-tos/read_grib_message_from_memory.ipynb`
- :ref:`/how-tos/read_file_list.ipynb`
