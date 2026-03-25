import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

ds_xr = ds.to_xarray()

# option1: writing to GRIB file using the accessor
ds_xr.earthkit.to_target("file", "_res_xarray_to_grib_2.grib")

# option2: writing to GRIB file using the top level function
ekd.to_target("file", "_res_xarray_to_grib_2a.grib", data=ds_xr)
