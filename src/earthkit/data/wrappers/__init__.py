# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import typing as T
from importlib import import_module

from earthkit.data.core import Base
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.decorators import locked

LOG = logging.getLogger(__name__)


class Wrapper(Base):
    def to_string(self):
        return f"{self.data}"

    def to_integer(self):
        return int(self.data)


# TODO: Add plugins
def _helpers(function_name, lookup, here=os.path.dirname(__file__), package=__name__):
    if not lookup:
        for path in os.listdir(here):
            if path.endswith(".py") and path[0] not in ("_", "."):
                name, _ = os.path.splitext(path)
                try:
                    lookup[name] = getattr(import_module(f".{name}", package=package), function_name)
                except Exception as e:
                    LOG.warning(f"Error loading {function_name} '{name}': {e}")
    return lookup


_WRAPPERS = {}


@locked
def _wrappers():
    return _helpers("wrapper", _WRAPPERS)


def get_wrapper(data, *args, **kwargs):
    """Returns the input object with the appropriate earthkit-data wrapper.
    i.e. so that an xarray object can be handled as an earkit-data object.
    """
    if isinstance(data, Base):
        return data

    for name, h in _wrappers().items():
        wrapper = h(data, *args, **kwargs)
        if wrapper is not None:
            return wrapper.mutate()
    else:
        fullname = ".".join([data.__class__.__module__, data.__class__.__qualname__])
        LOG.warning(f"Cannot find a wrapper for class: {fullname}, returning unwrapped object")
        return data


def call_wrapper_method(
    data: T.Any,
    method_name: str,
    *args,
    wrapper_kwargs=None,
    **method_kwargs,
) -> T.Any:
    """Check if a wrapper has a method and call it on the wrapper of the data object."""
    if wrapper_kwargs is None:
        wrapper_kwargs = {}
    wrapper_kwargs.setdefault("fieldlist", False)
    wrapper_kwargs.setdefault("try_dataset", False)
    wrapper = get_wrapper(data, **wrapper_kwargs)
    if not hasattr(wrapper, method_name):
        # LOG.warning(
        #     f"Wrapper for type {type(data)} does not have method {method_name}, returning original data"
        # )
        return data
    method = getattr(wrapper, method_name)
    result = method(*args, **method_kwargs)
    if isinstance(data, Base):
        return get_wrapper(result)
    return result
