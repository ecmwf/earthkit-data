.. _config:

Configuration
=============

*earthkit-data* is maintaining a global configuration.

The configuration is automatically loaded from and saved into a yaml file located at ``~/.config/earthkit/data/config.yaml``. An alternative path can be specified via the ``EARTHKIT_DATA_CONFIG_FILE`` environmental variable (it is only read at startup).

The configuration can be accessed and modified from Python. The configuration options can also be defined as :ref:`environment variables <config_env>`, which take precedence over the config file.

See the following notebooks for examples:

    - :ref:`/examples/config.ipynb`
    - :ref:`/examples/config_env_vars.ipynb`


.. _config_get:

Accessing configuration options
--------------------------------

The earthkit-data configuration can be accessed using the python API:

.. literalinclude:: include/config-get.py

.. warning::

    When an :ref:`environment variable <config_env>` is set, it takes precedence over the config parameter, and its value is returned from :func:`get() <config_get>`.

.. _config_set:

Changing configuration
-------------------------

.. note::

    It is recommended to restart your Jupyter kernels after changing
    or resetting config options.

The earthkit-data configuration can be modified using the python API:

.. literalinclude:: include/config-set.py

.. warning::

    When an :ref:`environment variable <config_env>` is set, the new value provided for :func:`set() <config_set>` is saved into the config file but :func:`get() <config_get>` wil still return the value of the environment variable. A warning is also generated.


.. _config_temporary:

Temporary configuration
------------------------

We can create a temporary configuration (as a context manager) as a copy of the original configuration. We will still refer to it as “config”, but it is completely independent from the original object and changes are not saved into the yaml file (even when ``config.autosave`` is True).

.. literalinclude:: include/config-temporary.py

Output::

    30
    5
    11

.. warning::

    When an :ref:`environment variable <config_env>` is set, the same rules applies as for :func:`set() <config_set>`.


.. _config_reset:

Resetting configuration
------------------------

.. note::

    It is recommended to restart your Jupyter kernels after changing
    or resetting the configuration.

The earthkit-data configuration can be reset using the python API:

.. literalinclude:: include/config-reset.py

.. warning::

    When an :ref:`environment variable <config_env>` is set, the same rules applies as for :func:`set() <config_set>`.


.. _config_env:

Environment variables
----------------------

Each configuration parameter has a corresponding environment variable (see the full list :ref:`here <config_env_table>`). When an environment variable is set, it takes precedence over the config parameter as the following examples show.

First, let us assume that the value of  ``url-download-timeout`` is 5 in the config file and no environment variable is set.

.. code-block:: python

    >>> from earthkit.data import config
    >>> config.get("url-download-timeout")
    30

Then, set the environment variable ``EARTHKIT_DATA_URL_DOWNLOAD_TIMEOUT``.

.. code-block:: bash

    export EARTHKIT_DATA_URL_DOWNLOAD_TIMEOUT=5

.. code-block:: python

    >>> from earthkit.data import config
    >>> config.get("url-download-timeout")
    5
    >>> config.env()
    {'url-download-timeout': ('EARTHKIT_DATA_URL_DOWNLOAD_TIMEOUT', '5')}
    >>> config.set("url-download-timeout", 10)
    UserWarning: Config option 'url-download-timeout' is also set by environment variable
    'EARTHKIT_DATA_URL_DOWNLOAD_TIMEOUT'.The environment variable takes precedence and
    its value is returned when calling get(). Still, the value set here will be
    saved to the config file.
    >>> config.get("url-download-timeout")
    5

Finally, unset the environment variable and check the config value again, which is now the value from the config file.

.. code-block:: bash

    unset EARTHKIT_DATA_URL_DOWNLOAD_TIMEOUT


.. code-block:: python

    >>> from earthkit.data import config
    >>> config.get("url-download-timeout")
    10


See also the following notebook:

    - :ref:`/examples/config_env_vars.ipynb`


.. _config_table:

List of configuration parameters
-----------------------------------

This is the list of all the config parameters:

.. module-output:: generate_config_rst


.. _config_env_table:

List of environment variables
---------------------------------

This is the list of the config environment variables:

.. module-output:: generate_config_env_rst
