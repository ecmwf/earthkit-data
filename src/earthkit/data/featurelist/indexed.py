# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import defaultdict

from earthkit.data.core.index import Index, MaskIndex, MultiIndex
from earthkit.data.core.order import build_remapping

from .featurelist import FeatureList


def create_fieldlist(fields=None):
    from earthkit.data.indexing.empty import EmptyFieldList
    from earthkit.data.indexing.simple import SimpleFieldList

    if fields is None or len(fields) == 0:
        return EmptyFieldList()
    else:
        return SimpleFieldList(fields)


class IndexFeatureListBase(Index, FeatureList):
    # @staticmethod
    # def from_fields(fields):
    #     r"""Create a :class:`SimpleFieldList`.

    #     Parameters
    #     ----------
    #     fields: iterable
    #         Iterable of :obj:`Field` objects.

    #     Returns
    #     -------
    #     :class:`SimpleFieldList`

    #     """
    #     from earthkit.data.indexing.simple import SimpleFieldList

    #     return SimpleFieldList.from_fields(fields)

    def get(
        self,
        keys,
        default=None,
        astype=None,
        raise_on_missing=False,
        output="auto",
        group_by_key=False,
        flatten_dict=False,
        remapping=None,
        patch=None,
    ):
        from earthkit.data.utils.args import metadata_argument_new

        keys, astype, default, keys_arg_type = metadata_argument_new(keys, astype=astype, default=default)

        if output == "auto":
            if keys_arg_type is not None:
                output = keys_arg_type
        elif output in [list, "list"]:
            output = list
        elif output in [tuple, "tuple"]:
            output = tuple
        elif output in [dict, "dict"]:
            output = dict
        else:
            raise ValueError(f"Invalid output: {output}")

        remapping = build_remapping(remapping, patch, forced_build=False)

        _kwargs = {
            "default": default,
            "raise_on_missing": raise_on_missing,
            "remapping": remapping,
            "flatten_dict": flatten_dict,
            # "patch": patch,
            "astype": astype,
        }

        if not group_by_key or output == "auto":
            return [f._get_fast(keys, output=output, **_kwargs) for f in self]
        else:
            if output is dict:
                result = defaultdict(list)
                for f in self:
                    r = f._get_fast(keys, output=dict, **_kwargs)
                    for k, v in r.items():
                        result[k].append(v)
                return dict(result)
            else:
                vals = [f._get_fast(keys, output=list, **_kwargs) for f in self]
                return [[x[i] for x in vals] for i in range(len(keys))]

    def metadata(self, keys, **kwargs):
        if isinstance(keys, str):
            keys = "metadata." + keys
        else:
            is_tuple = isinstance(keys, tuple)
            keys = ["metadata." + x for x in keys]
            if is_tuple:
                keys = tuple(keys)

        return self.get(keys, raise_on_missing=True, **kwargs)

    def _default_ls_keys(self):
        if len(self) > 0:
            return self[0].default_ls_keys
        return []

    def ls(self, n=None, keys="default", extra_keys=None, collections=None):
        from earthkit.data.utils.summary import ls as summary_ls

        def _proc(n: int, keys: str | list | tuple = None, collections: str | list | tuple = None):
            num = len(self)
            pos = slice(0, num)

            if n is not None:
                pos = slice(0, min(num, n)) if n > 0 else slice(num - min(num, -n), num)
            pos_range = range(pos.start, pos.stop)

            default = None
            astype = None
            if keys and len(pos_range) > 0:
                default = [None] * len(keys)
                astype = [None] * len(keys)

            for i in pos_range:
                r = self[i]._get_fast(
                    keys=keys,
                    default=default,
                    astype=astype,
                    collections=collections,
                    output=dict,
                    flatten_dict=True,
                )
                yield r

            # if component is not None:
            #     for i in pos_range:
            #         f = self[i]
            #         v = {}
            #         for ns_val in f._dump_component(component, prefix_keys=True, filter=filter).values():
            #             v.update(ns_val)
            #         if keys:
            #             v.update(f._get_fast(keys, default=default, astype=astype, output=dict))
            #         yield (v)
            # else:
            #     for i in pos_range:
            #         yield (self[i]._get_fast(keys, default=default, astype=astype, output=dict))

        if keys == "default":
            keys = self._default_ls_keys()

        return summary_ls(_proc, n=n, keys=keys, extra_keys=extra_keys, collections=collections)

    def head(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("head: n must be > 0")
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("n must be > 0")
        return self.ls(n=-n, **kwargs)

    def to_target(self, target, *args, **kwargs):
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def _default_encoder(self):
        return self[0]._default_encoder() if len(self) > 0 else None

    def _encode(self, encoder, hints=None, **kwargs):
        if hints and hints.get("path_allowed", False) and hasattr(self, "_encode_path"):
            result = self._encode_path(encoder, **kwargs)
            if result is not None:
                return result
        return self._encode_default(encoder, **kwargs)

    def _encode_default(self, encoder, *args, **kwargs):
        return encoder._encode_featurelist(self, *args, **kwargs)

    # def describe(self, *args, **kwargs):
    #     r"""Generate a summary of the fieldlist."""
    #     from earthkit.data.utils.summary import format_describe

    #     def _proc():
    #         for f in self:
    #             # PW: TODO: `default` and `astype` kwargs of `f._get_fast()` might need to be aligned with `keys`
    #             yield (f._get_fast(self._describe_keys, output=dict))

    #     return format_describe(_proc(), *args, **kwargs)

    # retur
    # def _normalise_sel_input(self, **kwargs):
    #     from .field import Field

    #     return Field._normalise_sel_input(**kwargs)

    # @staticmethod
    # def _normalise_key_values(**kwargs):
    #     from ..core.field import Field

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        pass
        # return MaskFieldList(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        pass
        # assert all(isinstance(_, IndexFieldListBase) for _ in sources)
        # return MultiFieldList(sources)


class MaskFeatureList(IndexFeatureListBase, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class MultiFeatureList(IndexFeatureListBase, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
