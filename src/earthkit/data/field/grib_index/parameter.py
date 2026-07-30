# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


class IndexParameterBuilder:
    """Builder for creating parameter components from MARS requests.

    This builder extracts parameter metadata from MARS request dictionaries and creates
    the appropriate parameter component subclass using :func:`create_parameter`.
    """

    @staticmethod
    def build(db, build_empty=False):
        from earthkit.data.field.component.parameter import create_parameter
        from earthkit.data.field.handler.parameter import ParameterFieldComponentHandler

        d = IndexParameterBuilder._build_dict(db)
        if not d and not build_empty:
            return None

        component = create_parameter(d)
        handler = ParameterFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(db):
        d = dict()
        for k, v in db.items():
            if k.startswith("parameter.") and v is not None:
                d[k[10:]] = v

        return d
