# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


#: Common CF coordinate names which can be mapped to an axis
AXES = {
    "x": ["x", "projection_x_coordinate", "lon", "longitude"],
    "y": ["y", "projection_y_coordinate", "lat", "latitude"],
    "z": ["height", "pressure", "level", "altitude", "depth"],
    "t": ["time", "valid_time", "forecast_reference_time"],
}


#: Common CF variable names which can be mapped to a vector component
COMPONENTS = {
    "u": ["u", "u_component_of_wind"],
    "v": ["v", "v_component_of_wind"],
}
