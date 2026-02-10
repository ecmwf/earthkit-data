# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def new_geotiff_field(band, da):
    r"""Create a Field object from GeoTIFF Xarray dataarray"""

    from earthkit.data.core.field import Field
    from earthkit.data.field.component.labels import SimpleLabels
    from earthkit.data.field.geotiff.data import GeoTIFFData
    from earthkit.data.field.geotiff.geography import GeoTIFFGeography
    from earthkit.data.field.parameter import ParameterFieldPart

    data = GeoTIFFData(da)
    parameter = ParameterFieldPart.from_dict({"variable": da.name})
    geography = GeoTIFFGeography(da)
    labels = SimpleLabels(band=band, **da.attrs)

    r = Field(
        data=data,
        parameter=parameter,
        time=None,
        geography=geography,
        vertical=None,
        ensemble=None,
        labels=labels,
    )

    # r._set_private_data("grib", grib)
    return r
