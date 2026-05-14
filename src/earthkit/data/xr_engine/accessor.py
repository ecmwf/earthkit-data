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

    @staticmethod
    def grid_spec_str(field):
        try:
            grid_spec = field.geography.grid_spec()
            from earthkit.data.utils import to_str

            return to_str(grid_spec)

        except Exception:
            return None

    def build(self, field):
        res = dict()
        grid_spec = self.grid_spec_str(field)

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

        return res

    def set_field(self, field, da_attrs):
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
        return res

    def set_grid_spec(self, grid_spec, da_attrs):
        from earthkit.data.utils import to_str

        res = dict()
        grid_spec_str = to_str(grid_spec)
        if grid_spec_str is None:
            raise ValueError(f"Invalid grid_spec: {grid_spec}")

        attrs_ori = da_attrs.get(self.ACCESSOR_KEY, dict())
        attrs = attrs_ori.copy()
        attrs["grid_spec"] = grid_spec_str

        res[self.ACCESSOR_KEY] = attrs

        return res
