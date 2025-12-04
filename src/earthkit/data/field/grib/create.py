# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.field.data import ArrayData


def new_grib_field(handle, data=None, cache=False):
    from earthkit.data.core.field import Field
    from earthkit.data.field.grib.data import GribData
    from earthkit.data.field.grib.ensemble import GribEnsemble
    from earthkit.data.field.grib.geography import GribGeography
    from earthkit.data.field.grib.labels import GribLabels
    from earthkit.data.field.grib.parameter import GribParameter
    from earthkit.data.field.grib.proc import GribProc
    from earthkit.data.field.grib.time import GribTime
    from earthkit.data.field.grib.vertical import GribVertical

    # from earthkit.data.specs.labels import SimpleLabels

    if data is None:
        data = GribData(handle)

    # parameter = GribParameter(handle)
    # time = GribTime(handle)
    # geography = GribGeography(handle)
    # vertical = GribVertical(handle)
    # labels = SimpleLabels()
    # ensemble = GribEnsemble(handle)
    # grib = GribLabels(handle)

    time = GribTime(handle)
    geography = GribGeography(handle)
    vertical = GribVertical(handle)
    ensemble = GribEnsemble(handle)
    proc = GribProc(handle)
    parameter = GribParameter(handle)
    grib = GribLabels(handle)

    r = Field(
        data=data,
        parameter=parameter,
        time=time,
        geography=geography,
        vertical=vertical,
        ensemble=ensemble,
        proc=proc,
        # labels=labels,
    )

    r._set_private_data("grib", grib)
    return r


def new_array_grib_field(
    field, handle, array_namespace=None, device=None, flatten=False, dtype=None, cache=False
):
    values = field.to_array(array_namespace=array_namespace, device=device, flatten=flatten, dtype=dtype)
    data = ArrayData(values)

    new_handle = handle.deflate()
    new_field = new_grib_field(new_handle, data=data, cache=cache)

    return new_field


def new_grib_field_from_buffer(buf):
    import eccodes

    from earthkit.data.new_field.grib.handle import MemoryGribHandle

    handle = eccodes.codes_new_from_message(buf)
    return new_grib_field(MemoryGribHandle.from_raw_handle(handle), cache=False)
