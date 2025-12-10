import earthkit.data as ekd

ds_fl = ekd.from_source("sample", "test.grib")

vals1 = ds_fl.to_array(array_backend="torch")
vals2 = ds_fl[0].to_array(array_backend="torch")
