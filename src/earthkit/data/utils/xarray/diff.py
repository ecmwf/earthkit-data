# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging
import math

LOG = logging.getLogger(__name__)


class DictDiffInfo:
    def __init__(self, same, diff_dict={}, diff_text=str()):
        self.same = same
        self.diff_dict = dict(**diff_dict)
        self.diff_text = diff_text


class DictDiff:
    @staticmethod
    def diff(vals1, vals2):
        if not isinstance(vals1, dict):
            raise ValueError(f"Unsupported type for vals1: {type(vals1)}. Expecting dict")

        if not isinstance(vals2, dict):
            raise ValueError(f"Unsupported type for vals2: {type(vals2)}. Expecting dict")

        diff_dict = {}
        if len(vals1) != len(vals2):
            return ListDiffInfo(False, ListDiff.VALUE_DIFF, f"Length mismatch: {len(vals1)} != {len(vals2)}")

        for k, v1 in vals1.items():
            if k not in vals2:
                diff_dict[k] = (None, v1)
            else:
                v2 = vals2[k]
                same, _ = ListDiff._compare(v1, v2)
                if not same:
                    diff_dict[k] = (v2, v1)

        if diff_dict:
            diff_text = ", ".join([f"{k}: {v[0]} != {v[1]}" for k, v in diff_dict.items()])
            return DictDiffInfo(False, diff_dict=diff_dict, diff_text=diff_text)
        else:
            return DictDiffInfo(True)


class ListDiffInfo:
    def __init__(self, same, diff_type=None, diff_text=str(), diff_index=-1):
        self.same = same
        self.type = diff_type
        self.diff_text = diff_text
        self.diff_index = diff_index


class ListDiff:
    VALUE_DIFF = 0
    TYPE_DIFF = 1

    @staticmethod
    def _compare(v1, v2):
        if isinstance(v1, int) and isinstance(v2, int):
            return v1 == v2, ListDiff.VALUE_DIFF
        elif isinstance(v1, float) and isinstance(v2, float):
            return math.isclose(v1, v2, rel_tol=1e-9), ListDiff.VALUE_DIFF
        elif isinstance(v1, str) and isinstance(v2, str):
            return v1 == v2, ListDiff.VALUE_DIFF
        elif isinstance(v1, datetime.timedelta) and isinstance(v2, datetime.timedelta):
            return v1 == v2, ListDiff.VALUE_DIFF
        elif type(v1) is not type(v2):
            return False, ListDiff.TYPE_DIFF
        else:
            raise ValueError(f"Unsupported type: {type(v1)}")

    @staticmethod
    def diff(vals1, vals2, name=str()):
        if not isinstance(vals1, (list, tuple)):
            raise ValueError(f"Unsupported type for vals1: {type(vals1)}. Expecting list/tuple")

        if not isinstance(vals2, (list, tuple)):
            raise ValueError(f"Unsupported type for vals2: {type(vals2)}. Expecting list/tuple")

        if len(vals1) != len(vals2):
            return ListDiffInfo(False, ListDiff.VALUE_DIFF, f"Length mismatch: {len(vals1)} != {len(vals2)}")

        for i, (v1, v2) in enumerate(zip(vals1, vals2)):
            same, diff = ListDiff._compare(v1, v2)
            if not same:
                if diff == ListDiff.VALUE_DIFF:
                    diff = f"Value mismatch at {name}[{i}]: {v1} != {v2}"
                elif diff == ListDiff.TYPE_DIFF:
                    diff = f"Type mismatch at {name}[{i}]: {type(v1)} != {type(v2)}"
                return ListDiffInfo(False, ListDiff.VALUE_DIFF, diff, i)
        return ListDiffInfo(True)


def check_coords(self, var_name, coord_name, coords, ref_coords):
    if coord_name in ref_coords:
        # from .diff import ListDiff
        from .diff import list_to_str

        v1 = ref_coords[coord_name].vals
        v2 = coords[coord_name]
        diff = ListDiff.diff(v1, v2, name=coord_name)
        if not diff.same:
            raise ValueError(
                (
                    f'Variable "{var_name}" has inconsistent dimension "{coord_name}" compared '
                    f"to other variables. Expected values: {list_to_str(v1)}, "
                    f"got: {list_to_str(v2)}. {diff.diff_text}"
                )
            )
