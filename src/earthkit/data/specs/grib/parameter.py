# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


class GribParameterBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.specs.parameter import SimpleParameter

        d = GribParameterBuilder._build_dict(handle)
        spec = SimpleParameter.from_dict(d)
        spec._set_private_data("handle", handle)
        return spec

    @staticmethod
    def _build_dict(handle):
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
            variable=name,
            units=units,
        )

    @staticmethod
    def get_grib_context(param, context):
        handle = param.private_data("handle")
        if handle is not None:
            if "handle" not in context:
                context["handle"] = handle
        else:
            r = {
                "shortName": param.name,
                # "units": param.units,
            }
        context.update(r)


# def create_from_grib(handle):
#     def _get(key, default=None):
#         return handle.get(key, default=default)

#     v = _get("shortName", None)
#     if v == "~":
#         v = handle.get("paramId", ktype=str, default=None)
#     if v is None:
#         v = _get("param", None)
#     name = v

#     units = _get("units", None)

#     d = dict(
#         variable=name,
#         units=units,
#     )

#     r = SimpleParameter.from_dict(d)
#     r._set_private_data("handle", handle)
#     return r


# def get_grib_context(spec, context):
#     if hasattr(spec, "handle"):
#         if "handle" not in context:
#             context["handle"] = spec.handle
#     else:
#         r = {
#             "shortName": spec.name,
#             # "units": spec.units,
#         }
#         context.update(r)
