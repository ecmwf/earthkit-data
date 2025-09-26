# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def new_xarray_field(handle, variable, selection=None):
    r"""Create a Field object from XArray"""
    pass
    # from earthkit.data.specs.geography import SimpleGeography
    # from earthkit.data.specs.labels import SimpleLabels
    # from earthkit.data.specs.parameter import Parameter
    # from earthkit.data.specs.time import Time
    # from earthkit.data.specs.vertical import Vertical
    # from earthkit.data.specs.xarray.data import XArrayData

    # data = XArrayData(variable, selection)
    # parameter = Parameter.from_xarray(variable, selection)
    # time = Time.from_xarray(variable, selection)
    # geography = SimpleGeography.from_xarray(variable, selection)
    # vertical = Vertical.from_xarray(variable, selection)
    # labels = SimpleLabels()

    # return cls(
    #     data=data,
    #     parameter=parameter,
    #     time=time,
    #     geography=geography,
    #     vertical=vertical,
    #     labels=labels,
    #     **kwargs,
    # )

    #
    #
    # from earthkit.data.core.field import Field
    # from earthkit.data.specs.grib.data import GribData
    # from earthkit.data.specs.grib.ensemble import GribEnsemble
    # from earthkit.data.specs.grib.geography import GribGeography
    # from earthkit.data.specs.grib.labels import GribLabels
    # from earthkit.data.specs.grib.parameter import GribParameter
    # from earthkit.data.specs.grib.time import GribTime
    # from earthkit.data.specs.grib.vertical import GribVertical
    # from earthkit.data.specs.labels import SimpleLabels

    # if data is None:
    #     data = GribData(handle)

    # parameter = GribParameter(handle)
    # time = GribTime(handle)
    # geography = GribGeography(handle)
    # vertical = GribVertical(handle)
    # labels = SimpleLabels()
    # ensemble = GribEnsemble(handle)
    # grib = GribLabels(handle)

    # r = Field(
    #     data=data,
    #     parameter=parameter,
    #     time=time,
    #     geography=geography,
    #     vertical=vertical,
    #     ensemble=ensemble,
    #     labels=labels,
    # )

    # r._set_private_data("grib", grib)
    # return r


# def new_array_grib_field(field, handle, array_backend=None, flatten=False, dtype=None, cache=False):
#     values = field.to_array(array_backend=array_backend, flatten=flatten, dtype=dtype)
#     data = ArrayData(values)

#     new_handle = handle.deflate()
#     new_field = new_grib_field(new_handle, data=data, cache=cache)

#     return new_field
