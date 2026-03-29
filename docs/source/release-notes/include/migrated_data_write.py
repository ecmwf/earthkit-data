import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

# case 1 - equivalent solutions
with open("res.grib", "wb") as f:
    ds.to_target("file", f)

with open("res.grib", "wb") as f:
    t = ekd.create_target("file", f)
    t.write(ds)

# case 2 - equivalent solutions
with open("res.grib", "wb") as f:
    for field in ds:
        field.to_target("file", f)

with open("res.grib", "wb") as f:
    t = ekd.create_target("file", f)
    for field in ds:
        t.write(field)
