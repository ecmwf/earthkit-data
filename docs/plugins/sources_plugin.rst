.. _sources_plugin:

Sources plugins
=============================

What is a source?
------------------

A :class:`Source` is a Python class in earthkit-data that can access data
from a given location or provider. There are several built-in :ref:`sources <data-sources>`, the most
common being the :ref:`file <data-sources-file>` source.

Adding a new source as a pip plugin
-------------------------------------

A **sources plugin** should contain a Python class inherited from :class:`earthkit.data.Source` to implement access for a custom data source. Let us suppose the new class is called "MyClass".

The name of the Python package containing the plugin should start with ``earthkit-data-`` and use "-". Let us call it "earthkit-data-my-source". We should be able to install this package as::

      pip install earthkit-data-my-source

The package to import should start with :py:class:`earthkit_data\_` and use "_". In our case this would be: "earthkit_data_my_source". We should be able to import the class from it as:

  .. code-block:: python

      from earthkit_data_my_source import MyClass

In the ``setup.cfg`` file of the package, we should have the ``entry_points``
integration as follow:

  .. code-block:: ini

      [options.entry_points]
      earthkit.data.sources =
          my-source = earthkit_data_my_source:MyClass


With this we could use the new source in :func:`from_source` as:

  .. code-block:: python

      import earthkit.data

      ds = earthkit.data.from_source("my-source", ...)


.. note::

  The source name used in :func:`from_source` is only defined in the ``entry_points`` block in ``setup.cfg``, so it is not deduced from the package name.


Example
-------

There is the ``earthkit-data-demo-source`` package with the code located at https://github.com/ecmwf/earthkit-data-demo-source demonstrating how to implement a ``sources plugin``.

This data source plugin allows accessing data from a SQL database using earthkit-data.

Once the package is installed either from source or from PyPI as::

    pip install earthkit-data-demo-source

tabular data can be read in earthkit-data as follows:

.. code-block:: python

    import earthkit.data

    ds = earthkit.from_source(
        "demo-source",
        "sqlite:///test.db",
        "select * from data;",
        parse_dates=["time"],
    )
    df = ds.to_pandas()

The integration is performed by ``entry_points`` is defined in  ``setup.cfg``.

  .. code-block:: ini

    [options.entry_points]
    earthkit.data.sources =
        demo-source = earthkit_data_demo_source:DemoSource
