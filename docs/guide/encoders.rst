.. _encoders:

Encoders
===============

An **encoder** is used to generate data in a suitable format that can be written/added to a :ref:`target <data-targets>`. Encoders are typically used implicitly via :func:`to_target` but we can also instantiate an :class:`Encoder` and work with it directly.

create_encoder()
---------------------------

We can create an :class:`Encoder` via :func:`create_encoder`.

.. py:function:: create_encoder(name, *args, **kwargs)

  Create an encoder specified by ``name`` .

  :param str name: the encoder. ``name`` can refer for a built-in encoder (see below) or an encoder plugin.
  :param tuple *args: specify encoder parameters
  :param dict **kwargs: specify additional encoder parameters.


Built in encoders
---------------------

**earthkit-data** has the following built-in encoders:

  .. list-table:: Data encoders
    :widths: 20 60 20
    :header-rows: 1

    * - Name
      - Description
      - Class
    * - grib
      - encode data as GRIB
      - :py:class:`GribEncoder`
    * - netcdf
      - encode data as NetCDF
      - :py:class:`NetCDFEncoder`
    * - geotiff
      - encode data as GeoTIFF
      - :py:class:`GeoTIFFEncoder`
    * - csv
      - encode data as CSV
      - :py:class:`CSVEncoder`


Examples
----------
    - :ref:`/examples/grib_encoder.ipynb`
