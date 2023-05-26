.. _caching:

Caching
=============

.. warning::

     This part of eartkit-data is still a work in progress. Documentation
     and code behaviour will change.

Purpose
-------

eartkit-data caches most of the remote data access on a local cache. Running again
``earthkit.data.from_source`` will use the cached data instead of
downloading it again. When the cache is full, cached data is deleted according it cache policy
(i.e. oldest data is deleted first).
earthkit-data cache configuration is managed through the :doc:`settings`.

.. warning::

    The earthkit-data cache is intended to be used by a single user.
    Sharing cache with **multiple users is not recommended**.
    Downloading a local copy of data on a shared disk to have multiple
    users working is a different use case and should be supported
    through using mirrors.

.. _cache_location:

Cache location
--------------

  The cache location is defined by the ``cache‑directory`` setting. Its default
  value depends on your system:

    - ``/tmp/earthkit-data-$USER`` for Linux,
    - ``C:\\Users\\$USER\\AppData\\Local\\Temp\\earthkit-data-$USER`` for Windows
    - ``/tmp/.../earthkit-data-$USER`` for MacOS


  The cache location can be read and modified either with shell command or within python.

  .. note::

    It is recommended to restart your Jupyter kernels after changing
    the cache location.


  From Python:

  .. code:: python

    >>> import earthkit.data
    >>> earthkit.data.settings.get(
    ...     "cache-directory"
    ... )  # Find the current cache directory
    /tmp/earthkit-data-$USER
    >>> # Change the value of the setting
    >>> earthkit.data.settings.set("cache-directory", "/big-disk/earthkit-data-cache")

    # Python kernel restarted

    >>> import earthkit.data
    >>> earthkit.data.settings.get(
    ...     "cache-directory"
    ... )  # Cache directory has been modified
    /big-disk/earthkit-data-cache

  More generally, the earthkit-data settings can be read, modified, reset
  to their default values from python,
  see the :doc:`Settings documentation <settings>`.

Cache limits
------------

Maximum-cache-size
  The ``maximum-cache-size`` setting ensures that earthkit-data does not
  use to much disk space.  Its value sets the maximum disk space used
  by earthkit-data cache.  When earthkit-data cache disk usage goes above
  this limit, earthkit-data triggers its cache cleaning mechanism  before
  downloading additional data.  The value of cache-maximum-size is
  absolute (such as "10G", "10M", "1K").

Maximum-cache-disk-usage
  The ``maximum-cache-disk-usage`` setting ensures that earthkit-data
  leaves does not fill your disk.
  Its values sets the maximum disk usage as % of the filesystem containing the cache
  directory. When the disk space goes below this limit, earthkit-data triggers
  its cache cleaning mechanism before downloading additional data.
  The value of maximum-cache-disk-usage is relative (such as "90%" or "100%").

.. warning::
    If your disk is filled by another application, earthkit-data will happily
    delete its cached data to make room for the other application as soon
    as it has a chance.

.. note::
    When tweaking the cache settings, it is recommended to set the
    ``maximum-cache-size`` to a value below the user disk quota (if applicable)
    and ``maximum-cache-disk-usage`` to ``None``.


Caching settings default values
-------------------------------

.. module-output:: generate_settings_rst .*-cache-.* cache-.*

Other earthkit-data settings can be found :ref:`here <settings_table>`.
