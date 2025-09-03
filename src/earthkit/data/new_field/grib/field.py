# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def new_grib_field(handle, cache=False):
    from earthkit.data.core.field import Field
    from earthkit.data.specs.grib.data import GribData
    from earthkit.data.specs.grib.geography import GribGeography
    from earthkit.data.specs.grib.labels import GribLabels
    from earthkit.data.specs.grib.parameter import GribParameterBuilder
    from earthkit.data.specs.grib.realisation import GribRealisationBuilder
    from earthkit.data.specs.grib.time import GribTimeBuilder
    from earthkit.data.specs.grib.vertical import GribVerticalBuilder
    from earthkit.data.specs.labels import SimpleLabels

    data = GribData(handle)
    parameter = GribParameterBuilder.build(handle)
    time = GribTimeBuilder.build(handle)
    geography = GribGeography(handle)
    vertical = GribVerticalBuilder.build(handle)
    labels = SimpleLabels()
    realisation = GribRealisationBuilder.build(handle)
    grib = GribLabels(handle)

    r = Field(
        data=data,
        parameter=parameter,
        time=time,
        geography=geography,
        vertical=vertical,
        realisation=realisation,
        labels=labels,
    )

    r._set_private_data("grib", grib)
    return r
