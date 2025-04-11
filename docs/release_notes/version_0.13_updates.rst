Version 0.13 Updates
/////////////////////////


Version 0.13.8
===============

Fixes
++++++++++

- Fixed issue when kwargs passed to the Xarray engine as a dict were modified in-place (:pr:`671`).


Version 0.13.7
===============

Fixes
++++++++++

- Fixed issue when Xarray created from GRIB with chunks failed in computations  (:pr:`669`).


Version 0.13.6
===============

This release reverts the changes introduced in version 0.13.5, which caused a regression (:issue:`663`). The issue will be addressed in a future release.


Version 0.13.5
===============

Fixes
++++++++++

- Fixed issue when NetCDF data with 1D latitudes/longitudes appearing as variables was not parsed into a fieldlist when read with :func:`from_source` (:pr:`658`).

.. warning::

    This release introduced a regression (:issue:`663`) and was reverted in version 0.13.6. The issue will be addressed in a future release.


Version 0.13.4
===============

Fixes
++++++++++

- Fixed issue when iterating through the keys and values in some BUFR messages failed with KeyError (:pr:`653`)


Version 0.13.3
===============

Fixes
++++++++++

- Fixed issue when could not convert ZIP containing a single NetCDF file to Xarray (:pr:`650`)


Version 0.13.2
===============

Fixes
++++++++++

- Fixed issue when could not read GRIB data from FDB streams in multiprocessing (:pr:`647`)


Version 0.13.1
===============

Fixes
++++++++++

- Fixed issue when :ref:`to_target() <targets-file>` could not assign an encoder to the ".grib1" and ".grib2" suffixes (:pr:`643`)


Version 0.13.0
===============

Deprecations
+++++++++++++++++++

- :ref:`deprecated-settings`
- :ref:`deprecated-auto-save-settings`
- :ref:`deprecated-data-save`
- :ref:`deprecated-data-write`
- :ref:`deprecated-new-grib-output`
- :ref:`deprecated-griboutput`
- :ref:`deprecated-new-grib-coder`
- :ref:`deprecated-gribcoder`

Configuration
++++++++++++++++++

- The "settings" has been renamed to :ref:`config <config>`. The API did not change with the exception of ``settings.auto_save_settings``, which now is ``config.autosave``. The "settings" object is still available for backward compatibility but will be removed in a future release. Users are encouraged to migrate the code to use ``config`` instead. (:pr:`586`)
- The configuration file changed to ``~/.config/earthkit/data/config.yaml``. When it is not available, the old configuration file at "~/.config/earthkit/settings.yaml" is loaded and saved into the new path. This is done until "settings" is removed.
- As new feature, the configuration file can be specified via the ``EARTHKIT_DATA_CONFIG_FILE`` environmental variable. The environmental variable takes precedence over the default configuration file (it is only read at startup).

See :ref:`here <deprecated-settings>` for more details.


New writer API
+++++++++++++++

- Introduced a new Writer API to facilitate the creation of custom data writers. It is based on :ref:`targets <targets>` that can represent a file, a database, a remote server etc and are able write data by using a suitable :ref:`encoder <encoders>` (:pr:`596`).
- The existing writing mechanisms are still kept ensuring backward compatibility, but marked deprecated and will be removed in a future release. For all deprecated methods/objects, see as follows:

  - :ref:`deprecated-data-save`
  - :ref:`deprecated-data-write`
  - :ref:`deprecated-new-grib-output`
  - :ref:`deprecated-griboutput`
  - :ref:`deprecated-new-grib-coder`
  - :ref:`deprecated-gribcoder`

See the notebook examples:

  - :ref:`/examples/file_target.ipynb`
  - :ref:`/examples/grib_to_file_target.ipynb`
  - :ref:`/examples/grib_to_file_pattern_target.ipynb`
  - :ref:`/examples/grib_to_fdb_target.ipynb`
  - :ref:`/examples/grib_to_geotiff.ipynb`
  - :ref:`/examples/grib_encoder.ipynb`

New features
+++++++++++++++++

- Refactored :ref:`data-sources-wekeo` and :ref:`data-sources-wekeocds` to use ``hda`` version 2 (:pr:`593`). The minimum ``hda`` version is now 2.22.
- Added support for patterns with dates using timedelta as ``strftimedlta()`` for the :ref:`data-sources-file-pattern` source (:pr:`606`)
- Enabled using string formatter for output file patterns in :ref:`new_grib_output <deprecated-new-grib-output>` and :ref:`GribOutput <deprecated-griboutput>` (:pr:`603`)
- Enabled creating :ref:`data-sources-lod` fieldlists without latitudes/longitudes (:pr:`636`)
- Added :py:meth:`cpu` to the torch backend (:pr:`578`)
