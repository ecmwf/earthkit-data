.. _data-sources-iris:

iris
-----

.. py:function:: from_source("iris", path, iris_open_kwargs=None, iris_save_kwargs=None, xr_load_kwargs=None)
  :noindex:

  The ``iris`` source accesses data from a file or directory using the `Iris <https://scitools-iris.readthedocs.io/en/latest/>`_ library,
  and converting to `Xarray <https://xarray.pydata.org/en/stable/>`_ via the `ncdata <https://ncdata.readthedocs.io/en/latest/>`_ package.

  :param str path: path to the file or directory
  :param dict iris_open_kwargs: keyword arguments passed to the ``iris.load`` method
  :param dict iris_save_kwargs: keyword arguments passed to the ``iris.save`` method for temporary conversion to NetCDF
  :param dict xr_load_kwargs: keyword arguments passed to the ``xarray.load`` method for loading the temporary NetCDF file

  .. note::

    This source requires the ``scitools-iris`` and ``ncdata`` packages to be installed.


  This reader also makes it possible to read data from ``.pp`` files supported by Iris with the :ref:`data-sources-file` source.

    .. code-block:: python

        import earthkit.data as ekd

        ds = ekd.from_source("file", "path/to/file.pp")
        ds.ls()


  The following example uses a pp file prepared as a :ref:`data-sources-sample`:

    .. code-block:: python

        >>> import earthkit.data as ekd
        >>> ds = ekd.from_source("sample", "air_temp.pp")
        >>> ds.ls()
            variable level       valid_datetime units
        0  air_temperature  None  1998-12-01T00:00:00     K


  Further examples:

    - :ref:`/examples/iris_pp.ipynb`
