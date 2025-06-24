import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

ds_xr = ds.to_xarray()

ds_xr.earthkit.to_grib("_res_xarray_to_grib_1.grib")
