Version 0.13 Updates
/////////////////////////


Version 0.13.0
===============

Configuration
++++++++++++++++++

- The "settings" has been renamed as :ref:`config <config>`. The API did not change with the exception of ``settings.auto_save_settings``, which now is ``config.autosave``. The "settings" object is still available for backward compatibility but will be removed in a future release. Users are encouraged to migrate the code to use ``config`` instead.
- The configuration file changed to ``~/.config/earthkit/data/config.yaml``. When it is not available, the old configuration file at "~/.config/earthkit/settings.yaml" is loaded and saved into the new path. This is done until "settings" is removed.
- As new feature, the configuration file can be specified via the ``EARTHKIT_DATA_CONFIG_FILE`` environmental variable. The environmental variable takes precedence over the default configuration file (it is only read at startup).

.. list-table:: Migrating form settings to config
   :header-rows: 1

   * - Settings (old code)
     - Config (new code)
   * -
       .. code-block:: python

           # the old import
           from earthkit.data import settings

           # the API is the same
           v = settings.get("number-of-download-threads")

           # the only change is related to autosave
           settings.auto_save_settings = False
     -
       .. code-block:: python

           # the new import
           from earthkit.data import config

           # the API is the same
           v = config.get("number-of-download-threads")

           # the only change is related to autosave
           config.autosave = False
