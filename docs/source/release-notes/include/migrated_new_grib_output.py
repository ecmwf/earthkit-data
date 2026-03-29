import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

# case 1
t = ekd.create_target(
    "file",
    "res.grib",
    metadata={"shortName": "2t", "generatingProcessIdentifier": 255},
)
for field in ds:
    t.write(field)

t.close()

# case 2 - equivalent solutions
t = ekd.create_target("file", "res.grib")
for field in ds:
    t.write(data=field, shortName="2t", generatingProcessIdentifier=255)
t.close()

t = ekd.create_target("file", "res.grib")
for field in ds:
    t.write(shortName="2t", template=field, generatingProcessIdentifier=255)
t.close()

# case 3
with ekd.create_target("file", "res.grib") as t:
    for field in ds:
        t.write(field, shortName="2t", generatingProcessIdentifier=255)

# case 4
with ekd.create_target("file", "res.grib") as t:
    for field in ds:
        values = field.values + 1
        t.write(data=field, values=values, shortName="2t")
