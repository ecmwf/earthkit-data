Version 0.13 Updates
/////////////////////////


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

- The "settings" has been renamed as :ref:`config <config>`. The API did not change with the exception of ``settings.auto_save_settings``, which now is ``config.autosave``. The "settings" object is still available for backward compatibility but will be removed in a future release. Users are encouraged to migrate the code to use ``config`` instead.
- The configuration file changed to ``~/.config/earthkit/data/config.yaml``. When it is not available, the old configuration file at "~/.config/earthkit/settings.yaml" is loaded and saved into the new path. This is done until "settings" is removed.
- As new feature, the configuration file can be specified via the ``EARTHKIT_DATA_CONFIG_FILE`` environmental variable. The environmental variable takes precedence over the default configuration file (it is only read at startup).

See :ref:`here <deprecated-settings>` for more details.


New writer API
+++++++++++++++

- Introduced a new Writer API to facilitate the creation of custom data writers. This API allows users to define how data should be written to various formats and destinations.
- The existing writing mechanisms have been refactored to use the new Writer API, ensuring backward compatibility while providing a more flexible and extensible framework for future enhancements.
