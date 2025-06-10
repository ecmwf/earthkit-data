# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging

LOG = logging.getLogger(__name__)


def normalize_selection(*args, **kwargs):
    from earthkit.data.arguments.transformers import ALL

    _kwargs = {}
    for a in args:
        if a is None:
            continue
        if isinstance(a, dict):
            _kwargs.update(a)
            continue
        raise ValueError(f"Cannot make a selection with {a}")

    _kwargs.update(kwargs)

    for k, v in _kwargs.items():
        assert (
            v is None
            or v is ALL
            or callable(v)
            or isinstance(v, (list, tuple, set, slice))
            or isinstance(v, (str, int, float, datetime.datetime, datetime.timedelta))
        ), f"Unsupported type: {type(v)} for key {k}"
    return _kwargs


def selection_from_index(coord_accessor, kwargs):
    if coord_accessor is None or not kwargs:
        return {}

    _kwargs = {}
    for k, v in kwargs.items():
        try:
            # the coords do not contain None
            coord_vals = coord_accessor(k)

            if len(coord_vals) == 0:
                return {}
            elif isinstance(v, slice):
                _kwargs[k] = coord_vals[v]
            elif isinstance(v, (list, tuple, set)):
                _kwargs[k] = [coord_vals[i] for i in v]
            elif isinstance(v, int):
                _kwargs[k] = coord_vals[v]
            else:
                raise ValueError(f"Invalid value index={v}. Type={type(v)} not supported")

        except IndexError as e:
            raise IndexError(
                (
                    f"Invalid index={v}. Index for key={k} must be in the range of"
                    f"(0, {len(coord_accessor(k))}) {e}"
                )
            )
    return _kwargs
