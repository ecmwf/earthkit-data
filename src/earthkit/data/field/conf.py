# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import namedtuple

from earthkit.data.field.data import Data
from earthkit.data.field.ensemble import EnsembleFieldMember
from earthkit.data.field.geography import GeographyFieldMember
from earthkit.data.field.parameter import ParameterFieldMember
from earthkit.data.field.spec.labels import SimpleLabels
from earthkit.data.field.time import TimeFieldMember
from earthkit.data.field.vertical import VerticalFieldMember

DATA = {"cls": Data, "name": "data", "direct": "values"}
TIME = {"cls": TimeFieldMember, "name": "time", "direct": all}
PARAMETER = {"cls": ParameterFieldMember, "name": "parameter", "direct": ("variable", "units")}
GEOGRAPHY = {"cls": GeographyFieldMember, "name": "geography"}
VERTICAL = {"cls": VerticalFieldMember, "name": "vertical", "direct": ("level", "layer")}
ENSEMBLE = {"cls": EnsembleFieldMember, "name": "ensemble", "direct": ("member",)}
LABELS = {"cls": SimpleLabels, "name": "labels"}

MEMBERS = {x["name"]: x for x in [DATA, TIME, PARAMETER, GEOGRAPHY, VERTICAL, ENSEMBLE, LABELS]}

for key, member in MEMBERS.items():
    assert key == member["cls"].NAME

MemberNames = namedtuple("MemberNames", list(MEMBERS.keys()))
NAMES = MemberNames(**{k: k for k in MEMBERS})


def init_member_conf(conf):

    def decorator(cls):
        keys = {}
        for member in MEMBERS.values():
            print(f"member: {member['name']} all keys: {member['cls'].ALL_KEYS}")
            member_cls = member["cls"]

            for key in member_cls.ALL_KEYS:
                # add key as a prefixed property
                method = member["name"] + "_" + key
                if getattr(cls, method, None) is None:

                    def _make(prop, member):
                        def _f(self):
                            return getattr(self._members[member], prop)

                        return _f

                    setattr(
                        cls,
                        method,
                        property(
                            fget=_make(key, member["name"]), doc=f"Return the {key} from .{member['name']}."
                        ),
                    )

                    keys[method] = (member["name"], key)
                    # print(f"  add property: {method} -> {member['name']}.{key}")

                # add allow using key with dot notation
                dot_key = member["name"] + "." + key
                keys[dot_key] = (member["name"], key)

                # print(f"  add dot key: {dot_key} -> {member['name']}.{key}")

            # some module keys are added as properties without a prefix
            direct_keys = member.get("direct", ())
            if direct_keys is all:
                direct_keys = member_cls.ALL_KEYS
            if isinstance(direct_keys, str):
                direct_keys = (direct_keys,)

            for key in direct_keys:
                if not hasattr(member_cls, key):
                    raise ValueError(f"Direct key {key} not found in module {member_cls}")

                if key in keys:
                    raise ValueError(f"Direct key {key} already defined in/for another member")

                if getattr(cls, key, None) is not None:
                    raise ValueError(f"Direct key {key} already defined in class {cls}")

                def _make(prop, member):
                    print("member=", member, "prop=", prop)

                    def _f(self):
                        return getattr(self._members[member], prop)

                    return _f

                setattr(
                    cls,
                    key,
                    property(
                        fget=_make(key, member["name"]), doc=f"Return the {key} from .{member['name']}."
                    ),
                )

                keys[key] = (member["name"], key)
                # print(f"  add direct property: {key} -> {member['name']}.{key}")

        cls._MEMBER_KEYS = keys

        print(f"MEMBER_KEYS for {cls}: {cls._MEMBER_KEYS}")
        return cls

    return decorator
