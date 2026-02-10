# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def init_part_conf(conf):

    PARTS = conf

    def decorator(cls):
        keys = {}
        for part_name, part in PARTS.items():
            if part is None:
                continue

            part_cls = cls._DEFAULT_PART_CLS.get(part_name)

            if part_cls is None:
                raise ValueError(f"Part {part_name} not found in class {cls}")

            for key in part_cls.ALL_KEYS:
                # add key as a prefixed property
                # method = part_name + "_" + key
                # if getattr(cls, method, None) is None:

                #     def _make(prop, part):
                #         def _f(self):
                #             return getattr(self._parts[part], prop)

                #         return _f

                #     setattr(
                #         cls,
                #         method,
                #         property(fget=_make(key, part_name), doc=f"Return the {key} from .{part_name}."),
                #     )

                #     keys[method] = (part_name, key)
                #     # print(f"  add property: {method} -> {part['name']}.{key}")

                # add allow using key with dot notation
                dot_key = part_name + "." + key
                keys[dot_key] = (part_name, key)

                # print(f"  add dot key: {dot_key} -> {part['name']}.{key}")

                # some module keys are added as properties without a prefix

                # direct_keys = component.get("direct", ())
                # if direct_keys is all:
                #     direct_keys = part_cls.ALL_KEYS
                # if isinstance(direct_keys, str):
                #     direct_keys = (direct_keys,)

                # for key in direct_keys:
                #     if not hasattr(part_cls, key):
                #         raise ValueError(f"Direct key {key} not found in module {part_cls}")

                #     if key in keys:
                #         raise ValueError(f"Direct key {key} already defined in/for another part")

                #     if getattr(cls, key, None) is not None:
                #         raise ValueError(f"Direct key {key} already defined in class {cls}")

                #     def _make(prop, part):
                #         def _f(self):
                #             return getattr(self._parts[part], prop)

                #         return _f

                #     setattr(
                #         cls,
                #         key,
                #         property(fget=_make(key, part_name), doc=f"Return the {key} from .{part_name}."),
                #     )

                # keys[key] = (part_name, key)
                # print(f"  add direct property: {key} -> {part_name}.{key}")

        cls._PART_KEYS = keys

        # PartNames = namedtuple("PartNames", list(PARTS.keys()))
        # setattr(cls, "_PART_NAMES", PartNames(**{k: k for k in PARTS}))

        return cls

    return decorator
