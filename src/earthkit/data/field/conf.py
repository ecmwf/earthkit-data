# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import namedtuple

# DATA = {"cls": Data, "name": "data", "direct": "values"}
# TIME = {"cls": TimeFieldMember, "name": "time", "direct": all}
# PARAMETER = {"cls": ParameterFieldMember, "name": "parameter", "direct": ("variable", "units")}
# GEOGRAPHY = {"cls": GeographyFieldMember, "name": "geography"}
# VERTICAL = {"cls": VerticalFieldMember, "name": "vertical", "direct": ("level", "layer")}
# ENSEMBLE = {"cls": EnsembleFieldMember, "name": "ensemble", "direct": ("member",)}
# LABELS = {"cls": SimpleLabels, "name": "labels"}

# MEMBERS = {x["name"]: x for x in [DATA, TIME, PARAMETER, GEOGRAPHY, VERTICAL, ENSEMBLE, LABELS]}

# for key, member in MEMBERS.items():
#     assert key == member["cls"].NAME

# MemberNames = namedtuple("MemberNames", list(MEMBERS.keys()))
# NAMES = MemberNames(**{k: k for k in MEMBERS})


def init_member_conf(conf):

    MEMBERS = conf

    def decorator(cls):
        keys = {}
        for member_name, member in MEMBERS.items():
            if member is None:
                continue

            member_cls = member["cls"]

            for key in member_cls.ALL_KEYS:
                # add key as a prefixed property
                method = member_name + "_" + key
                if getattr(cls, method, None) is None:

                    def _make(prop, member):
                        def _f(self):
                            return getattr(self._members[member], prop)

                        return _f

                    setattr(
                        cls,
                        method,
                        property(fget=_make(key, member_name), doc=f"Return the {key} from .{member_name}."),
                    )

                    keys[method] = (member_name, key)
                    # print(f"  add property: {method} -> {member['name']}.{key}")

                # add allow using key with dot notation
                dot_key = member_name + "." + key
                keys[dot_key] = (member_name, key)

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
                    def _f(self):
                        return getattr(self._members[member], prop)

                    return _f

                setattr(
                    cls,
                    key,
                    property(fget=_make(key, member_name), doc=f"Return the {key} from .{member_name}."),
                )

                keys[key] = (member_name, key)
                # print(f"  add direct property: {key} -> {member_name}.{key}")

        cls._MEMBER_KEYS = keys

        MemberNames = namedtuple("MemberNames", list(MEMBERS.keys()))
        setattr(cls, "_MEMBER_NAMES", MemberNames(**{k: k for k in MEMBERS}))

        # print(f"Initialized Field member configuration:")
        # print(f"_MEMBER_NAMES={cls._MEMBER_NAMES}")
        # print(f"_MEMBER_KEYS:")
        # for k, v in cls._MEMBER_KEYS.items():
        #     print(f" {k} -> {v}")

        return cls

    return decorator
