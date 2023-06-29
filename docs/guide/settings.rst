.. _settings:

Settings
========

*earthkit-data* is maintaining a set of global settings which control
its behaviour.

The settings are saved in ``~/.earthkit-data/settings.yaml``. They can
be accessed from Python.

Accessing settings
------------------

earthkit-data settings can be accessed using the python API:

.. literalinclude:: include/settings-1-get.py


Changing settings
-----------------

.. note::

    It is recommended to restart your Jupyter kernels after changing
    or resetting settings.

earthkit-data settings can be modified using the python API:

.. literalinclude:: include/settings-2-set.py


Resetting settings
------------------

.. note::

    It is recommended to restart your Jupyter kernels after changing
    or resetting settings.

earthkit-data settings can be reset using the python API:

.. literalinclude:: include/settings-3-reset.py


.. _settings_table:

Default values
--------------

.. module-output:: generate_settings_rst
