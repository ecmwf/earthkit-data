# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


class EarthkitAttrsBuilder:
    ACCESSOR_KEY = "_earthkit"
    VARIABLE_GRID_SPEC_KEY = "earthkit_grid_spec"

    @staticmethod
    def grid_spec_str(field):
        try:
            grid_spec = field.geography.grid_spec()
            if grid_spec is not None:
                import json

                return json.dumps(grid_spec)
            return None

        except Exception:
            return None

    # def build_variable_grid_spec_attr(self, field):
    #     grid_spec = self.grid_spec_str(field)
    #     if grid_spec is not None:
    #         return {self.VARIABLE_GRID_SPEC_KEY: grid_spec}
    #     return dict()

    def build(self, field, add_earthkit_attrs=True):
        res = dict()
        grid_spec = self.grid_spec_str(field)

        if add_earthkit_attrs:
            bpv = None
            try:
                md = field._get_grib().message(deflate=True)
                bpv = field._get_grib().get_extra_key("bitsPerValue", default=None)
                if bpv is None:
                    bpv = field.get("metadata.bitsPerValue", default=None)
            except Exception:
                md = ""

            attrs = {
                "message": md,
            }

            if bpv is not None and bpv != 0:
                attrs["bitsPerValue"] = bpv

            if grid_spec is not None:
                attrs["grid_spec"] = grid_spec

            res[self.ACCESSOR_KEY] = attrs

        # if grid_spec is not None:
        #     res[self.VARIABLE_GRID_SPEC_KEY] = grid_spec

        return res

    def set(self, field, da_attrs):
        res = dict()

        grid_spec = self.grid_spec_str(field)

        attrs_ori = da_attrs.get(self.ACCESSOR_KEY, dict())
        attrs = attrs_ori.copy()

        if attrs_ori:
            try:
                message = field._get_grib().message(deflate=True)
            except Exception:
                message = ""

        if message:
            attrs["message"] = message
        else:
            del attrs["message"]

        if grid_spec is not None:
            attrs["grid_spec"] = grid_spec
        elif "grid_spec" in attrs:
            del attrs["grid_spec"]

        res[self.ACCESSOR_KEY] = attrs

        if grid_spec is not None:
            res[self.VARIABLE_GRID_SPEC_KEY] = grid_spec
        elif self.VARIABLE_GRID_SPEC_KEY in res:
            res[self.VARIABLE_GRID_SPEC_KEY] = None

        return res
