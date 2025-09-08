# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .collector import GribContextCollector


class GribRealisationBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.specs.realisation import SimpleRealisation

        d = GribRealisationBuilder._build_dict(handle)
        spec = SimpleRealisation.from_dict(d)
        spec._set_private_data("handle", handle)
        return spec

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        v = _get("number")
        if v is None:
            v = _get("perturbationNumber")

        return dict(
            number=v,
        )


class GribRealisationContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(spec, context):
        r = {
            "number": spec.number,
        }
        context.update(r)
