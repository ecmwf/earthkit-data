.. _howtos:

Howtos
============


How to save results from a retrieval into a file?
--------------------------------------------------------------

You need to use the :func:`save` method on the resulting object. For example, this is how to
save the results of a :ref:`MARS retrieval <data-sources-mars>` into a file:

.. code-block:: python

    import earthkit.data as ekd

    ds = ekd.from_source(
        "mars",
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -10, 40, 10],  # N,W,S,E
        grid=[2, 2],
        date="2023-05-10",
    )

    ds.to_target("file", "my_data.grib")


How to convert GRIB to Xarray?
--------------------------------------------------------------

You can convert GRIB data to Xarray by calling :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` on
a GRIB fieldlist object. See :ref:`xr_engine` for details.


How to call to_xarray() with arguments for NetCDF data?
---------------------------------------------------------

When calling :func:`to_xarray` for NetCDF data it calls ``xarray.open_mfdataset`` internally. You can pass arguments to this xarray function by using the ``xarray_open_mfdataset_kwargs`` option. For example:


.. code-block:: python

    import earthkit.data as ekd

    req = {
        "format": "zip",
        "origin": "c3s",
        "sensor": "olci",
        "version": "1_1",
        "year": "2022",
        "month": "04",
        "nominal_day": "01",
        "variable": "pixel_variables",
        "region": "europe",
    }

    ds = ekd.from_source("cds", "satellite-fire-burned-area", req)
    r = ds.to_xarray(
        xarray_open_mfdataset_kwargs=dict(decode_cf=False, decode_times=False)
    )
