import earthkit.data as ekd
from earthkit.data.readers.grib.output import new_grib_coder

ds = ekd.from_source("sample", "test.grib")

values = ds[1].values + 1

# case 1
c = new_grib_coder()
# c is a GribCodesHandle
d = c.encode(values, shortName="2t", template=ds[1])

# case 2
c = new_grib_coder(template=ds[1])
# c is a GribCodesHandle
d = c.encode(values, shortName="2t")
