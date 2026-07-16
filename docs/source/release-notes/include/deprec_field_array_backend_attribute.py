import earthkit.data as ekd

ds_fl = ekd.from_source("sample", "test.grib")

b = ds_fl[0].array_backend
