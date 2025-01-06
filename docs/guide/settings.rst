.. _settings:

Settings
========

*earthkit-data* is maintaining a set of global settings which control
its behaviour.

The settings are automatically loaded from and saved into ``~/.earthkit-data/settings.yaml`` and they can
be accessed and modified from Python. The settings can also be defined as :ref:`environment variables <settings_env>`, which take precedence over the settings file.

See the following notebooks for examples:

    - :ref:`/examples/settings.ipynb`
    - :ref:`/examples/settings_env_vars.ipynb`


.. _settings_get:

Accessing settings
------------------

earthkit-data settings can be accessed using the python API:

.. literalinclude:: include/settings-get.py

.. warning::

    When an :ref:`environment variable <settings_env>` is set, it takes precedence over the settings parameter, and its value is returned from :func:`get() <settings_get>`.

.. _settings_set:

Changing settings
------------------

.. note::

    It is recommended to restart your Jupyter kernels after changing
    or resetting settings.

earthkit-data settings can be modified using the python API:

.. literalinclude:: include/settings-set.py

.. warning::

    When an :ref:`environment variable <settings_env>` is set, the new value provided for :func:`set() <settings_set>` is saved into the settings file but :func:`get() <settings_get>` wil still return the value of the environment variable. A warning is also generated.


.. _settings_temporary:

Temporary settings
------------------

We can create a temporary settings (as a context manager) as a copy of the original settings. We will still refer to it as “settings”, but it is completely independent from the original object and changes are not saved into the yaml file (even when ``settings.auto_save_settings`` is True).

.. literalinclude:: include/settings-temporary.py

Output::

    8
    12
    11

.. warning::

    When an :ref:`environment variable <settings_env>` is set, the same rules applies as for :func:`set() <settings_set>`.


.. _settings_reset:

Resetting settings
------------------

.. note::

    It is recommended to restart your Jupyter kernels after changing
    or resetting settings.

earthkit-data settings can be reset using the python API:

.. literalinclude:: include/settings-reset.py

.. warning::

    When an :ref:`environment variable <settings_env>` is set, the same rules applies as for :func:`set() <settings_set>`.


.. _settings_env:

Environment variables
----------------------

Each settings parameter has a corresponding environment variable (see the full list :ref:`here <settings_env_table>`). When an environment variable is set, it takes precedence over the settings parameter as the following examples show.

First, let us assume that the value of  ``number-of-download-threads`` is 5 in the settings file and no environment variable is set.

.. code-block:: python

    >>> from earthkit.data import settings
    >>> settings.get("number-of-download-threads")
    5

Then, set the environment variable ``EARTHKIT_DATA_NUMBER_OF_DOWNLOAD_THREADS``.

.. code-block:: bash

    export EARTHKIT_DATA_NUMBER_OF_DOWNLOAD_THREADS=26


.. code-block:: python

    >>> from earthkit.data import settings
    >>> settings.get("number-of-download-threads")
    26
    >>> settings.env()
    {'number-of-download-threads': ('EARTHKIT_DATA_NUMBER_OF_DOWNLOAD_THREADS', '26')}
    >>> settings.set("number-of-download-threads", 10)
    UserWarning: Setting 'number-of-download-threads' is also set by environment variable
    'EARTHKIT_DATA_NUMBER_OF_DOWNLOAD_THREADS'.The environment variable takes precedence and
    its value is returned when calling get(). Still, the value set here will be
    saved to the settings file.
    >>> settings.get("number-of-download-threads")
    26

Finally, unset the environment variable and check the settings value again, which is now the value from the settings file.

.. code-block:: bash

    unset EARTHKIT_DATA_NUMBER_OF_DOWNLOAD_THREADS


.. code-block:: python

    >>> from earthkit.data import settings
    >>> settings.get("number-of-download-threads")
    10


See also the following notebook:

    - :ref:`/examples/settings_env_vars.ipynb`


.. _settings_table:

List of settings parameters
----------------------------

This is the list of all the settings parameters:

.. module-output:: generate_settings_rst


.. _settings_env_table:

List of environment variables
---------------------------------

This is the list of the settings environment variables:

.. module-output:: generate_settings_env_rst
