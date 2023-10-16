.. _plugins-reference:

Earthkit-data Plugin mechanism
===============================

This document discusses how plugins are integrated into earthkit-data. There are two ways to add
a plugin into earthkit-data:

- A Python package using the standard `Python plugin <https://packaging.python.org/guides/creating-and-discovering-plugins>`_
  mechanism based on ``entry_points``. This is the generic earthkit-data plugin mechanism.

- A YAML file can be also be used to create plugins, when the plugin is simple enough
  and used only generic predefined code.
  (currently only for :doc:`dataset plugins </contributing/datasets>`).

Plugin as python packages using ``entry_points``
------------------------------------------------

During the installation of the pip package, the plugin registers itself thanks to
the entry points in its ``setup.cfg`` file, making earthkit-data aware of the new capabilities.
Then, the user can take advantage of the shared code through the enhanced
:py:func:`from_dataset()`, :py:func:`from_source()` etc. methods.

The following example shows how it can be done.

:Example:

    Let us suppose our package is called **earthkit-data-package-name** and implements a ``"sources"``  (note the plural form) plugin type . If it is  a ``pip`` package using ``setuptools`` we need to add an ``entry_points`` block to ``setup.cfg``:

    .. code-block:: ini

        [options.entry_points]
        earthkit.data.sources =
            foo = earthkit_data_package_name:FooClass
            bar = earthkit_data_package_name:BarClass

    This block specifies that in the package the :py:class:`FooClass` class implements the ``"foo"`` source, while
    the :py:class:`BarClass` class implements the ``"bar"`` source. In earthkit-data we will be able to use them as:

    .. code-block:: python

        from earthkit.data import from_source

        ds1 = from_source("foo", args1)
        ds2 = from_source("bar", args2)


For the other plugin types the ``entry_points`` configuration works exactly in the same way but we need to use ``earthkit.data.<plugintype>``. The supported plugin types are as follows:

      - :ref:`"datasets" <datasets>`
      - :ref:`"sources" <sources>`


See the individual documentation for each plugin type for detailed examples and
the standard `Python plugin documentation <https://packaging.python.org/guides/creating-and-discovering-plugins>`_.


Plugin as YAML files
--------------------

.. warning::

  This is still a work-in-progress.

Additionally, for :doc:`dataset plugins </contributing/datasets>` only, earthkit-data
search for known locations to find a YAML file with a name matching the requested dataset.
The YAML files are used to create an appropriate class.
