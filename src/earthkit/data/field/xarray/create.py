# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def new_xarray_field(variable, selection=None):
    r"""Create a Field object from XArray"""

    from earthkit.data.core.field import Field
    from earthkit.data.field.spec.labels import SimpleLabels
    from earthkit.data.field.xarray.data import XArrayData
    from earthkit.data.field.xarray.ensemble import XArrayEnsemble
    from earthkit.data.field.xarray.geography import XArrayGeography
    from earthkit.data.field.xarray.parameter import XArrayParameter
    from earthkit.data.field.xarray.time import XArrayTime
    from earthkit.data.field.xarray.vertical import XArrayVertical

    data = XArrayData(variable, selection)
    ensemble = XArrayEnsemble(variable, selection)
    parameter = XArrayParameter(variable, selection)
    time = XArrayTime(variable, selection)
    geography = XArrayGeography(variable, selection)
    vertical = XArrayVertical(variable, selection)
    labels = SimpleLabels()

    r = Field(
        data=data,
        parameter=parameter,
        time=time,
        geography=geography,
        vertical=vertical,
        ensemble=ensemble,
        labels=labels,
    )

    # r._set_private_data("grib", grib)
    return r
