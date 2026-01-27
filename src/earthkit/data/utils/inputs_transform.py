# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import inspect
import logging
import types
import typing as T
from functools import wraps

from earthkit.data import transform
from earthkit.data.wrappers import Wrapper

LOG = logging.getLogger(__name__)

try:
    UNION_TYPES = [T.Union, types.UnionType]
except AttributeError:
    # types.UnionType is not in versions of python<3.9
    UNION_TYPES = [
        T.Union,
    ]

EMPTY_TYPES = [inspect._empty]


# Consider moving these to earthkit-utils
def _ensure_iterable(input_item):
    """Ensure that an item is iterable."""
    if not isinstance(input_item, (tuple, list, dict)):
        return [input_item]
    return input_item


def _ensure_tuple(input_item):
    """Ensure that an item is a tuple."""
    if not isinstance(input_item, tuple):
        return tuple(_ensure_iterable(input_item))
    return input_item


def transform_inputs_decorator(
    kwarg_types: T.Dict[str, T.Any] = {},
    convert_types: T.Union[None, T.Tuple[T.Any], T.Dict[str, T.Tuple[T.Any]]] = None,
    ensure_units: T.Union[None, T.Dict[str, str]] = None,
    provenance: bool = False,
) -> T.Callable:
    """Transform the inputs to a function to match the requirements.

    Parameters
    ----------
    kwarg_types : Dict[str, type]
        Mapping of accepted object types for each arg/kwarg, this is to provide kwarg types in the case
        of an untyped function, or to override the function signature.
    convert_types : Tuple[type] or Dict[str, Tuple[type]]
        Data types to try to convert, in cases where the function is flexible and can handle multiple
        types which are not specified by the type-setting. For example, numpy functions can often handle
        numpy, pandas and xarray data objects. If a dict, applies per-argument.
    ensure_units : Dict[str, str]
        Ensure that the given arguments have the specified units. If the argument is a Wrapper object,
        the convert_units method will be called with the target unit.
    provenance : bool
        Whether to add provenance information to the output data. The end user should be able to set this
        option.

    Returns
    -------
    Callable
        Wrapped function.
    """
    if convert_types is None:
        convert_types = {}

    def decorator(function: T.Callable) -> T.Callable:
        def _wrapper(_kwarg_types, _convert_types, *args, **kwargs):
            _kwarg_types = {**_kwarg_types}
            signature = inspect.signature(function)
            mapping = signature_mapping(signature, _kwarg_types)

            # Store positional arg names for extraction later
            arg_names = []
            for arg, name in zip(args, signature.parameters):
                print(arg, name)
                arg_names.append(name)
                kwargs[name] = arg


            # Split args into multiple
            if len(args) < len(expected_args):
            
            
            convert_kwargs = [k for k in kwargs if k in mapping]

            # Filter for convert_types
            if _convert_types:
                if not isinstance(_convert_types, dict):
                    _convert_types = {key: _convert_types for key in convert_kwargs}

                convert_kwargs = [
                    k
                    for k in convert_kwargs
                    if isinstance(kwargs[k], _ensure_tuple(_convert_types.get(k, ())))
                ]

            # Split single input into many
            
            # Transform args/kwargs
            for key in convert_kwargs:
                value = kwargs[key]
                types_allowed = _ensure_iterable(mapping[key])
                if type(value) not in types_allowed:
                    for target_type in types_allowed:
                        try:
                            kwargs[key] = transform(value, target_type)
                        except Exception:
                            continue
                        break
            
            # Ensure units
            if ensure_units:
                for key, target_unit in ensure_units.items():
                    if key in kwargs:
                        value = kwargs[key]
                        if isinstance(value, Wrapper):
                            print('Convert units called')
                            # try:
                            #     kwargs[key] = value.convert_units(target_unit)
                            # except Exception:
                            #     pass
            
            # Expand Wrapper objects
            for k, v in list(kwargs.items()):
                if isinstance(v, Wrapper):
                    try:
                        kwargs[k] = v.data
                    except Exception:
                        pass

            # Extract positional args again
            args = [kwargs.pop(name) for name in arg_names]
            result = function(*args, **kwargs)
            
            # Add provenance here
            if provenance:
                pass
            
            return result

        @wraps(function)
        def wrapper(*args, _auto_inputs_transform=True, **kwargs):
            if not _auto_inputs_transform:
                return function(*args, **kwargs)
            return _wrapper(kwarg_types, convert_types, *args, **kwargs)

        return wrapper

    return decorator


def signature_mapping(signature, kwarg_types):
    """Map args and kwargs to object types.

    Uses hierarchical selection method:
    1. Explicitly defined type
    2. Based on Type setting in function
    3. Do nothing
    """
    mapping = {}
    for key, parameter in signature.parameters.items():
        if key in kwarg_types:
            # 1. Use explicitly defined type[s]
            kwarg_type = kwarg_types.get(key)
        elif parameter.annotation not in EMPTY_TYPES:
            # 2. Use type setting from function
            kwarg_type = parameter.annotation
            if T.get_origin(kwarg_type) in UNION_TYPES:
                # Need to expand union_types to list
                kwarg_type = T.get_args(kwarg_type)
        else:
            # 3. Do nothing, cannot assign None, as None is a valid type
            continue
        mapping[key] = kwarg_type
    return mapping
