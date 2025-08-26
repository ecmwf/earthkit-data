# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from ..parameter import Parameter


def from_grib(handle):
    def _get(key, default=None):
        return handle.get(key, default=default)

    v = _get("shortName", None)
    if v == "~":
        v = handle.get("paramId", ktype=str, default=None)
    if v is None:
        v = _get("param", None)
    name = v

    units = _get("units", None)

    return dict(
        name=name,
        units=units,
    )


def to_grib(spec, altered=True):
    if isinstance(spec, Parameter):
        if altered:
            if hasattr(spec, "_handle"):
                return {}
        return {
            "shortName": spec.name,
            # "units": spec.units,
        }
    raise TypeError("Expected a Parameter instance.")
