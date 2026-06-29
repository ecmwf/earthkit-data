.. _encoders:

Encoders
========

An **encoder** converts data into a serialisable format that can be written to a
:ref:`target <targets>`. Encoders are most commonly used implicitly through
:func:`~earthkit.data.to_target`, but can also be created and used directly.

.. note::

   The encoders are still under development. The most advanced encoder is the :ref:`grib_encoder`, which can handle a variety of data types. Currently, the other encoders only support trivial encoding of data into a serialisable format. For example, the NetCDF encoder simply calls :py:func:`xarray.to_netcdf` on an xarray Dataset/DataArray.

Creating an encoder
-------------------

Use :func:`~earthkit.data.encoders.create_encoder` to instantiate an encoder by name:

.. code-block:: python

    >>> from earthkit.data import create_encoder
    >>> enc = create_encoder("grib")
    >>> enc = create_encoder("grib", template=my_field, shortName="2t")

.. py:function:: create_encoder(name, *args, **kwargs)

   Create an encoder identified by *name*.

   :param str name: Name of an encoder (see table below).
   :param args: Positional arguments forwarded to the encoder constructor.
   :param kwargs: Keyword arguments forwarded to the encoder constructor.
   :rtype: Encoder


Common constructor parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All encoders accept the following keyword arguments in their constructors:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``template``
     - A default template object used as the basis for encoding. The exact accepted types depend on the encoder.
   * - ``metadata``
     - A dictionary of default metadata applied to every encoded item. Metadata supplied
       directly to :meth:`Encoder.encode` is merged on top, with the per-call values taking
       precedence.
   * - ``**kwargs``
     - Any additional keyword arguments are interpreted as metadata keys and merged into
       ``metadata``.


Encoding data
-------------

All encoders expose an :meth:`encode` method:

.. code-block:: python

    >>> enc = create_encoder("grib", template=field)
    >>> result = enc.encode(values=arr, shortName="2t", step=6)
    >>> result.to_file(open("out.grib", "wb"))

.. py:method:: Encoder.encode(data=None, values=None, metadata={}, template=None, check_nans=False, missing_value=9999, target=None, **kwargs)

   Encode *data* and return an :class:`EncodedData` object.

   :param data: Earthkit data object to encode (Field, FieldList, xarray Dataset/DataArray, …).
   :param values: Raw values array to encode.
   :param dict metadata: Per-call metadata merged on top of the encoder's default metadata.
   :param template: Per-call template overriding the encoder's default template.
   :param bool check_nans: Replace ``NaN`` values with *missing_value* before encoding.
   :param missing_value: Replacement value used when *check_nans* is ``True``.
   :param target: Target object; some encoders use this to optimise the output format.
   :rtype: EncodedData


Automatic encoder selection
----------------------------

When writing to a file target without specifying an encoder explicitly, the encoder is
selected automatically from the file extension:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Extension(s)
     - Encoder
   * - ``.grib``, ``.grb``, ``.grib1``, ``.grib2``, ``.grb1``, ``.grb2``
     - ``grib``
   * - ``.nc``, ``.nc3``, ``.nc4``, ``.netcdf``
     - ``netcdf``
   * - ``.tiff``, ``.tif``
     - ``geotiff``
   * - ``.bufr``
     - ``bufr``
   * - ``.odb``
     - ``odb``


Available encoders
-----------------

.. list-table::
   :header-rows: 1
   :widths: 16 52 32

   * - Name
     - Description
     - Class
   * - ``grib``
     - Encode data as GRIB. Supports Fields, FieldLists, and NumPy arrays. Requires a
       template or sufficient metadata to construct a valid GRIB message.
     - :py:class:`~earthkit.data.encoders.grib.GribEncoder`
   * - ``netcdf``
     - Encode data as NetCDF via xarray. Accepts Fields, FieldLists, and xarray
       Datasets/DataArrays.
     - :py:class:`~earthkit.data.encoders.netcdf.NetCDFEncoder`
   * - ``geotiff``
     - Encode data as GeoTIFF. Requires geo-referenced raster data.
     - :py:class:`~earthkit.data.encoders.geotiff.GeoTIFFEncoder`
   * - ``csv``
     - Encode tabular data as comma-separated values.
     - :py:class:`~earthkit.data.encoders.csv.CSVEncoder`
   * - ``bufr``
     - Encode data as BUFR (Binary Universal Form for the Representation of meteorological
       data).
     - :py:class:`~earthkit.data.encoders.bufr.BufrEncoder`
   * - ``odb``
     - Encode data as ODB (Observational DataBase) format.
     - :py:class:`~earthkit.data.encoders.odb.ODBEncoder`
   * - ``zarr``
     - Encode data as a Zarr array store.
     - :py:class:`~earthkit.data.encoders.zarr.ZarrEncoder`
   * - ``covjson``
     - Encode data as CoverageJSON (CovJSON).
     - :py:class:`~earthkit.data.encoders.covjson.CovJsonEncoder`
   * - ``geojson``
     - Encode data as GeoJSON.
     - :py:class:`~earthkit.data.encoders.geojson.GeoJsonEncoder`
   * - ``pp``
     - Encode data as Met Office PP (UM binary) format.
     - :py:class:`~earthkit.data.encoders.pp.PPEncoder`
   * - ``text``
     - Encode data as plain text.
     - :py:class:`~earthkit.data.encoders.text.TextEncoder`



Examples
--------

- :ref:`/tutorials/target/grib_encoder.ipynb`
