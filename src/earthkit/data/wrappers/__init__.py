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
        if wrapper is not None:  # and not hasattr(wrapper, "fields"):
            return wrapper.mutate()
    else:
        fullname = ".".join([data.__class__.__module__, data.__class__.__qualname__])
        LOG.warning(f"Cannot find a wrapper for class: {fullname}, returning unwrapped object")
        return data


def convert_units(
    *args,
    source_units: str | None = None,
    target_units: str | None = None,
    units_mapping: dict[str, str] | None = None,
    **kwargs,
):
    """Executing wrapper for the get_translator class method"""
    kwargs.setdefault("fieldlist", False)
    kwargs.setdefault("try_dataset", False)
    wrapper = get_wrapper(*args, **kwargs)
    return wrapper.convert_units(
        source_units=source_units,
        target_units=target_units,
        units_mapping=units_mapping,
    )


def update_metadata(
    data: T.Any,
    metadata_model: str | dict[str, T.Any] | None = None,
    provenance_metadata: dict[str, str | dict[str, str]] | None = None,
) -> T.Any:
    """Update the metadata of the data object with the given provenance metadata."""
    wrapper = get_wrapper(data, fieldlist=False, try_dataset=False)
    if not hasattr(wrapper, "update_metadata"):
        LOG.warning(
            f"Wrapper for type {type(data)} does not support metadata update, returning original data"
        )
        return data
    return wrapper.update_metadata(metadata_model=metadata_model, provenance_metadata=provenance_metadata)
