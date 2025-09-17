# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.specs.data import ArrayData


def new_grib_field(handle, data=None, cache=False):
    from earthkit.data.core.field import Field
    from earthkit.data.specs.grib.data import GribData
    from earthkit.data.specs.grib.ensemble import GribEnsemble
    from earthkit.data.specs.grib.geography import GribGeography
    from earthkit.data.specs.grib.labels import GribLabels
    from earthkit.data.specs.grib.parameter import GribParameter
    from earthkit.data.specs.grib.time import GribTime
    from earthkit.data.specs.grib.vertical import GribVertical
    from earthkit.data.specs.labels import SimpleLabels

    if data is None:
        data = GribData(handle)

    parameter = GribParameter(handle)
    time = GribTime(handle)
    geography = GribGeography(handle)
    vertical = GribVertical(handle)
    labels = SimpleLabels()
    ensemble = GribEnsemble(handle)
    grib = GribLabels(handle)

    r = Field(
        data=data,
        parameter=parameter,
        time=time,
        geography=geography,
        vertical=vertical,
        ensemble=ensemble,
        labels=labels,
    )

    r._set_private_data("grib", grib)
    return r


def new_array_grib_field(field, handle, array_backend=None, flatten=False, dtype=None, cache=False):
    values = field.to_array(array_backend=array_backend, flatten=flatten, dtype=dtype)
    data = ArrayData(values)

    new_handle = handle.deflate()
    new_field = new_grib_field(new_handle, data=data, cache=cache)

    return new_field
