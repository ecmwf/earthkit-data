import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

# case 1
ds.save("res.grib")

# case 2
ds.save("res.grib", append=True)

# case 3
ds.save("res.grib", bits_per_value=12)

# case 4
for field in ds:
    field.save("res1.grib", append=True, bits_per_value=12)
