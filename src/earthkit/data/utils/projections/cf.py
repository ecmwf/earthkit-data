# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


CF_PARAMS_TO_KWARGS = {
    "latitude_of_projection_origin": "central_latitude",
    "longitude_of_projection_origin": "central_longitude",
    "longitude_of_central_meridian": "central_longitude",
    "grid_north_pole_latitude": "pole_latitude",
    "grid_north_pole_longitude": "pole_longitude",
    "north_pole_grid_longitude": "central_rotated_longitude",
    "perspective_point_height": "satellite_height",
    "scale_factor_at_projection_origin": "scale_factor",
    "scale_factor_at_central_meridian": "scale_factor",
    "standard_parallel": "standard_parallels",
    "false_easting": "false_easting",
    "false_northing": "false_northing",
}


CF_PARAMS_TO_GLOBE_KWARGS = {
    "semi_major_axis": "semimajor_axis",
    "semi_minor_axis": "semiminor_axis",
    "inverse_flattening": "inverse_flattening",
}


def to_projection_kwargs(parameters):
    kwargs = {
        CF_PARAMS_TO_KWARGS.get(key): value
        for key, value in parameters.items()
        if key in CF_PARAMS_TO_KWARGS and key not in CF_PARAMS_TO_GLOBE_KWARGS
    }

    if not isinstance(kwargs.get("standard_parallels", []), list):
        kwargs["standard_parallels"] = [kwargs["standard_parallels"]]

    globe_kwargs = {
        CF_PARAMS_TO_GLOBE_KWARGS.get(key, key): value
        for key, value in parameters.items()
        if key in CF_PARAMS_TO_GLOBE_KWARGS
    }

    kwargs["globe"] = globe_kwargs

    return kwargs
