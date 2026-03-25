import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

# case 1 - equivalent solutions
t = ekd.create_target("file-pattern", "res_{shortName}.grib")
for field in ds:
    t.write(field)

t.close()

ds.to_target("file-pattern", "res_{shortName}.grib")
