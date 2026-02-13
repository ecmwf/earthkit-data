# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def new_mars_field(request, data=None, values=None, geography=None, reference_field=None):
    r"""Create a Field object from XArray"""

    from earthkit.data.core.field import Field
    from earthkit.data.field.data import ArrayFieldDataComponentHandler
    from earthkit.data.field.labels import SimpleLabels
    from earthkit.data.field.mars.ensemble import MarsEnsembleBuilder

    # from earthkit.data.field.mars.geography import MarsGeographyBuilder
    from earthkit.data.field.mars.parameter import MarsParameterBuilder
    from earthkit.data.field.mars.time import MarsTimeBuilder
    from earthkit.data.field.mars.vertical import MarsVerticalBuilder

    if values is not None:
        data = ArrayFieldDataComponentHandler(values)
    else:
        data = None

    if geography is None:
        pass
        # geography = MarsGeographyBuilder.build(request)

    ensemble = MarsEnsembleBuilder.build(request)
    parameter = MarsParameterBuilder.build(request)
    time = MarsTimeBuilder.build(request)
    vertical = MarsVerticalBuilder.build(request)
    labels = SimpleLabels({"mars": request})

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
