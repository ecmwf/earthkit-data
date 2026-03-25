import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

# case 1
o = ekd.new_grib_output("res_{shortName}.grib", split_output=True)
for field in ds:
    o.write(None, template=field)
o.close()
