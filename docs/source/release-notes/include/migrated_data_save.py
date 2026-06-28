import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

# case 1
ds.to_target("file", "res.grib")

# case 2
ds.to_target("file", "res.grib", append=True)

# case 3
ds.to_target("file", "res.grib", metadata={"bitsPerValue": 12})

# case 4 - equivalent solutions
with ekd.create_target("file", "res1.grib") as t:
    for field in ds:
        t.write(field, metadata={"bitsPerValue": 12})

with ekd.create_target("file", "res1.grib", metadata={"bitsPerValue": 12}) as t:
    for field in ds:
        t.write(field)

with ekd.create_target("file", "res1.grib") as t:
    for field in ds:
        t.write(field, bitsPerValue=12)
