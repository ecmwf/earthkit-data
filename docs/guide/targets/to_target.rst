.. _to-target:

to_target()
====================

We can write data to a given target by using :func:`to_target`. It can be either invoked on a :ref:`data object <data-object>` or the :ref:`data object <data-object>` can be specified as ``data``.

.. py:function:: to_target(name, *args, data=None, **kwargs)

  Write data to the target specified by ``name`` .

  :param str name: the target (see below)
  :param tuple *args: specify target parameters
  :param data: specify the :ref:`data object <data-object>` to write. Cannot be set when :func:`to_target` is called on a data object.
  :param dict **kwargs: specify additional target parameters. Also specify the encoder parameters.


.. _built-in-targets:


Built in targets
---------------------

**earthkit-data** has the following built-in targets:

  .. list-table::
    :widths: 20 60 20
    :header-rows: 1

    * - Name
      - Description
      - Class
    * - :ref:`targets-file`
      - write data to a file/files
      - :py:class:`~data.targets.FileTarget`
    * - :ref:`targets-file-pattern`
      - write data to multiple files based on a filename pattern
      - :py:class:`~data.targets.FilePatternTarget`
    * - :ref:`targets-fdb`
      - add data to a `Fields DataBase <https://fields-database.readthedocs.io/en/latest/>`_ (FDB)
      - :py:class:`~data.targets.FDBTarget`
    * - :ref:`targets-zarr`
      - add data to a `zarr <https://zarr.dev>`_ store
      - :py:class:`~data.targets.ZarrTarget`



.. _targets-file:

file
----

.. py:function:: to_target("file", file, append=False, data=None, encoder=None, template=None, metadata=None, **kwargs)
  :noindex:

  The ``file`` target writes data into a file.

  :param file:  The file path or file-like object to write to. When None, tries to guess the file name from the ``data`` if it is passed as a kwarg. When the file name cannot be constructed, a ValueError is raised. When ``file`` is a path, a file object is automatically created and closed when the target is closed. When ``file`` is a file-like object, its ownership is not transferred to the target. As a consequence, the file-like object is not closed when the writing is finished and :func:`to_target` returns.
  :type file: str, file-like object, None
  :param bool append:  If True, the file is opened in append mode. Only used if ``file`` is a path.
  :param data: specify the data to write. Cannot be set when :func:`to_target` is called on a data object.
  :param encoder: The encoder to use to encode the data. When it is a str, the encoder is looked up in
    the available :ref:`encoders <encoders>`. When None, the encoder type will be determined from the data
    to write (if possible), from the target file suffix or from the :class:`Target` properties. When a
    suitable encoder cannot be instantiated a ValueError is raise.
  :type encoder: str, :py:class:`Encoder`, None
  :param template: The template to be used by the encoder.
  :type template: obj, None
  :param dict **kwargs: other keyword arguments passed to the encoder


  .. code-block:: python

      import earthkit.data as ekd

      # read GRIB data into a fieldlist.
      ds = ekd.from_source("sample", "test.grib")

      # write first field
      ds[0].to_target("file", "_my_res_1.grib")

      # write whole fieldlist
      ds.to_target("file", "_my_res_2.grib")


  Notebook examples:

    - :ref:`/examples/file_target.ipynb`
    - :ref:`/examples/grib_to_file_target.ipynb`
    - :ref:`/examples/grib_to_file_pattern_target.ipynb`
    - :ref:`/examples/grib_to_geotiff.ipynb`

.. _targets-file-pattern:

file-pattern
------------

.. py:function:: to_target("file-pattern", file, append=False, data=None, encoder=None, template=None, metadata=None, **kwargs)
  :noindex:

  The ``file-pattern`` target writes data into multiple files based on a filename pattern.

  :param file: The file path to write to. The output file name defines a pattern containing metadata keys in the format of ``{key}``. Each data item (e.g. a field) will be written into a file with a name created by substituting the relevant metadata values in the filename pattern.
  :type file: str
  :param bool append:  If True, the files are opened in append mode.
  :param data: specify the data to write. Cannot be set when :func:`to_target` is called on a data object.
  :param encoder: The encoder to use to encode the data. When it is a str, the encoder is looked up in
    the available :ref:`encoders <encoders>`. When None, the encoder type will be determined from the data
    to write (if possible), from the target file suffix or from the :class:`Target` properties. When a suitable encoder cannot be instantiated a ValueError is raised.
  :type encoder: str, :py:class:`Encoder`, None
  :param template: The template to be used by the encoder.
  :type template: obj, None
  :param dict **kwargs: other keyword arguments passed to the encoder


  .. code-block:: python

      import earthkit.data as ekd

      # read GRIB data into a fieldlist.
      # Contains 2 fields: msl and 2t
      ds = ekd.from_source("sample", "test.grib")

      # this code results in 2 files: _my_res_msl.grib and _my_res_2t.grib
      ds.to_target("file-pattern", "_my_res_{shortName}.grib")


  Notebook examples:

    - :ref:`/examples/grib_to_file_pattern_target.ipynb`


.. _targets-fdb:

fdb
----

.. py:function:: to_target("fdb", fdb=None, config=None, userconfig=None, data=None, encoder=None, template=None, metadata=None, **kwargs)
  :noindex:

  The ``fdb`` target writes to an `FDB (Fields DataBase) <https://fields-database.readthedocs.io/en/latest/>`_, which is a domain-specific object store developed at ECMWF for storing, indexing and retrieving GRIB data. earthkit-data uses the `pyfdb <https://pyfdb.readthedocs.io/en/latest>`_ package to add data to FDB.

  :param fdb: the FDB to write to
  :type fdb: pyfdb.FDB, None
  :param dict,str config: the FDB configuration directly passed to ``pyfdb.FDB()``. If not provided, the configuration is either read from the environment or the default configuration is used. Only used if no ``fdb`` is specified.
  :param dict,str userconfig: the FDB user configuration directly passed to ``pyfdb.FDB()``. If not provided, the configuration is either read from the environment or the default configuration is used. Only used if no ``fdb`` is specified.
  :param data: specify the data to write. Cannot be set when :func:`to_target` is called on a data object.
  :param encoder: The encoder to use to encode the data. When it is a str, the encoder is looked up in
    the available :ref:`encoders <encoders>`. When None, the encoder type will be determined from the data
    to write (if possible) or from the :class:`Target` properties. When a suitable encoder cannot be instantiated a ValueError is raised.
  :type encoder: str, :py:class:`Encoder`, None
  :param template: The template to be used by the encoder.
  :type template: obj, None
  :param dict **kwargs: other keyword arguments passed to the encoder


  .. code-block:: python

      import earthkit.data as ekd

      ds = ekd.from_source("sample", "tuv_pl.grib")

      # config contains the FDB configuration

      # writing a field
      ds[0].to_target("fdb", config=config)

      # writing a whole fieldlist
      ds.to_target("fdb", config=config)


  Notebook examples:

    - :ref:`/examples/grib_to_fdb_target.ipynb`


.. _targets-zarr:

zarr
----

.. py:function:: to_target("zarr", earthkit_to_xarray_kwargs=None, xarray_to_zarr_kwargs=None, data=None)
  :noindex:

  The ``zarr`` target writes to a `Zarr <https://zarr.readthedocs.io/en/stable/>`_ store.

  :param dict earthkit_to_xarray_kwargs: the keyword arguments passed to the :func:`to_xarray` function. If not provided, the default values are used.
  :param dict xarray_to_zarr_kwargs: the keyword arguments passed to the :py:func:`xarray.Dataset.to_zarr` function. As a bare minimum, the ``store`` keyword argument must be provided.
  :param data: specify the data to write. Cannot be set when :func:`to_target` is called on a data object.

  This target converts the data to an :ref:`xarray.Dataset <xarray-dataset>` and then writes it to a Zarr store using the :py:func:`xarray.Dataset.to_zarr` function. The conversion to an Xarray dataset is done by the :func:`to_xarray` function.

  Notebook examples:

    - :ref:`/examples/grib_to_zarr_target.ipynb`


.. .. _data-targets-multio:

.. multio
.. ------

.. .. py:function:: to_target("multio", plan=None, data=None, template=None, metadata=None, **kwargs)
..   :noindex:

..   :param plan:  Multio plan
..   :type plan: Client, os.PathLike, str, dict
..   :param data: specify the data to write. Cannot be set when :func:`to_target` is called on a data object.
..   :param template: The template to be used by the encoder.
..   :type template: obj, None
..   :param dict **kwargs: other keyword arguments passed to the encoder
