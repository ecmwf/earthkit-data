import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

# case 1
o = ekd.new_grib_output("res.grib", shortName="2t")
for field in ds:
    o.write(None, template=field)
o.close()

# case 2
o = ekd.new_grib_output("res.grib")
for field in ds:
    o.write(None, shortName="2t", template=field)
o.close()

# case 3
with ekd.new_grib_output("res.grib") as o:
    for field in ds:
        o.write(None, shortName="2t", template=field)

# case 4
with ekd.new_grib_output("res.grib") as o:
    for field in ds:
        values = field.values + 1
        o.write(values, shortName="2t", template=field)
