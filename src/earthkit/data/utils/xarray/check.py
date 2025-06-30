# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import math

from .diff import DictDiff
from .diff import ListDiff

LOG = logging.getLogger(__name__)


def list_to_str(vals, n=10):
    try:
        size = f"({len(vals)}) "
        if len(vals) <= n:
            return size + str(vals)
        else:
            lst = size + "[" + ", ".join(str(vals[: n - 1])) + "..., " + str(vals[-1]) + "]"
            return lst
    except Exception:
        return vals


def check_coords(var_name, coord_name, coords, ref_coords):
    if coord_name in ref_coords:
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


class CubeChecker:
    def __init__(self, tensor):
        self.tensor = tensor

    def first_diff(self, coord_keys):
        for i, f in enumerate(self.tensor.source):
            t_coords = self.tensor._index_to_coords_value(i, self.tensor)
            f_coords = f.metadata(coord_keys)
            print(f"Checking field[{i}] with coords {t_coords} vs {f_coords}")
            diff = ListDiff.diff(t_coords, f_coords)
            if not diff.same:
                name = ""
                if diff.diff_index != -1:
                    name = coord_keys[diff.diff_index]

                return i, f, t_coords, f_coords, name, diff

    def neighbour_field(self, field_num, index):
        f_other = None
        index_other = None
        if index > 0:
            index_other = index - 1
        elif index < field_num - 1:
            index_other = index + 1
        if index_other is not None:
            f_other = self.tensor.source[index_other]

        return f_other, index_other

    def namespace_diff(self, f, f_other, namespace):
        meta = f.metadata(namespace=namespace)
        meta_other = f_other.metadata(namespace=namespace)
        return DictDiff.diff(meta, meta_other)

    def meta_diff(self, f, f_other, coords_keys):
        f_coords = f.metadata(coords_keys)
        other_coords = f_other.metadata(coords_keys)
        meta = {coords_keys[i]: v for i, v in enumerate(f_coords)}
        meta_other = {coords_keys[i]: v for i, v in enumerate(other_coords)}
        return DictDiff.diff(meta, meta_other)

    def meta(self, f, coords_keys):
        f_coords = f.metadata(coords_keys)
        return {coords_keys[i]: v for i, v in enumerate(f_coords)}

    def check(self, details=False):
        field_num = len(self.tensor.source)
        cube_num = math.prod(self.tensor._user_shape)

        if field_num == cube_num:
            return

        coord_keys = list(self.tensor._user_coords.keys())
        dims = "\n".join([f"{k} {list_to_str(v)}" for k, v in self.tensor._user_coords.items()])
        text_num = (
            f"Input does not form a full hypercube."
            f" Expected number of fields based on the dimensions does not match "
            f"actual number of fields: {cube_num} != {field_num}.\n"
            f"Dimensions: \n {dims}"
        )

        print(text_num)
        print(coord_keys)

        if not details:
            raise ValueError(text_num)
        else:
            # find first differing field
            r = self.first_diff(coord_keys)
            if r is not None:
                index, f, t_coords, f_coords, name, diff = r
                assert index is not None
                assert index >= 0

                text_dims = (
                    f"\nFirst difference from the expected dimensions occurs at field[{index}]"
                    f' for dimension "{name}". Expected {t_coords[diff.diff_index]}'
                    f" got {f_coords[diff.diff_index]}."
                )

                f_other, index_other = self.neighbour_field(field_num, index)
                if f_other is not None:
                    assert index_other is not None
                    assert index_other >= 0
                    assert index_other != index

                    # namespace diff
                    namespaces = ["mars", "ls", "time", "vertical", "geography"]
                    md_diff = {}
                    diff = self.meta_diff(f, f_other, coord_keys)
                    if not diff.same:
                        md_diff["dims"] = diff.diff_text

                    for ns in namespaces:
                        diff = self.namespace_diff(f, f_other, ns)
                        if not diff.same:
                            md_diff[f"namespace={ns}"] = diff.diff_text

                    text_ns = (
                        f"\nComparing field[{index}] with field[{index_other}], the following "
                        "metadata difference was found:\n"
                    )
                    for k, v in md_diff.items():
                        text_ns += f"{k}:\n {v}\n"

                md = {}
                md["dims"] = self.meta(f, coord_keys)
                for ns in namespaces:
                    md["namespace=" + ns] = f.metadata(namespace=ns)

                text_meta = f"\nField[{index}] metadata:\n"
                for k, v in md.items():
                    text_meta += f"{k}:\n {v}\n"

                raise ValueError(f"{text_num}{text_dims}{text_ns}{text_meta}")
