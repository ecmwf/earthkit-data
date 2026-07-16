import earthkit.data as ekd

ds = ekd.from_source("sample", "test.grib")

values = ds[1].values + 1

# case 1 - equivalent solutions
c = ekd.create_encoder("grib")
d = c.encode(
    values=values,
    template=ds[1],
    shortName="2t",
    generatingProcessIdentifier=255,
)
# d is a GribEncodedData

c = ekd.create_encoder("grib")
d = c.encode(ds[1], values=values, shortName="2t", generatingProcessIdentifier=255)

# case 2
c = ekd.create_encoder("grib", template=ds[1], generatingProcessIdentifier=255)
d = c.encode(
    values=values,
    shortName="2t",
)
