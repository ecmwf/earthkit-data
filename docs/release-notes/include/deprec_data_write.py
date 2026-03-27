import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

# case 1
with open("res.grib", "wb") as f:
    ds.write(f)

# case 2
with open("res.grib", "wb") as f:
    for field in ds:
        field.write(f)
