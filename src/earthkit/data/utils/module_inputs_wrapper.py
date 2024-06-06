# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Module containing methods to transform the inputs of functions based on the function type setting,
common signitures or mapping defined at call time
"""
import inspect
import types
import typing as T
from functools import wraps

from earthkit.data import transform
from earthkit.data.wrappers import Wrapper

try:
    UNION_TYPES = [T.Union, types.UnionType]
except AttributeError:
    # types.UnionType is not in versions of python<3.9
    UNION_TYPES = [
        T.Union,
    ]

EMPTY_TYPES = [inspect._empty]


def _ensure_iterable(input_item):
    """Ensure that an item is iterable"""
    if not isinstance(input_item, (tuple, list, dict)):
        return [input_item]
    return input_item


def _ensure_tuple(input_item):
    """Ensure that an item is a tuple"""
    if not isinstance(input_item, tuple):
        return tuple(_ensure_iterable(input_item))
    return input_item


def transform_function_inputs(
    function: T.Callable,
    kwarg_types: T.Dict[str, T.Any] = {},
    convert_types: T.Union[T.Tuple[T.Any], T.Dict[str, T.Tuple[T.Any]]] = (),
) -> T.Callable:
    """Transform the inputs to a function to match the requirements.
    earthkit.data handles the input arg/kwarg format.

    Parameters
    ----------
    function : Callable
        Method to be wrapped
    kwarg_types : Dict[str: type]
        Mapping of accepted object types for each arg/kwarg
    convert_types : Tuple[type]
        List of data-types to try to convert, this can be useful when the function is versitile and can
        accept a large number of data-types, hence only a small number of types should be converted.

    Returns
    -------
    [type]
        [description]
    """

    def _wrapper(kwarg_types, convert_types, *args, **kwargs):
        kwarg_types = {**kwarg_types}
        signature = inspect.signature(function)
        mapping = signature_mapping(signature, kwarg_types)

        # Add args to kwargs for ease of looping:
        arg_names = []
        for arg, name in zip(args, signature.parameters):
            arg_names.append(name)
            kwargs[name] = arg

        convert_kwargs = [k for k in kwargs if k in mapping]
        # Only convert some data-types, this can be used to prevent conversion for for functions which
        #  accept a long-list of formats, e.g. numpy methods can accept xarray, pandas and more

        # Filter for convert_types
        if convert_types:
            # Ensure convert_types is a dictionary
            if not isinstance(convert_types, dict):
                convert_types = {key: convert_types for key in convert_kwargs}

            convert_kwargs = [
                k for k in convert_kwargs if isinstance(kwargs[k], _ensure_tuple(convert_types.get(k, ())))
            ]

        # transform args/kwargs
        for key in convert_kwargs:
            value = kwargs[key]
            kwarg_types = _ensure_iterable(mapping[key])
            # Transform value if necessary
            if type(value) not in kwarg_types:
                for kwarg_type in kwarg_types:
                    try:
                        kwargs[key] = transform(value, kwarg_type)
                    except Exception:
                        # Transform was not possible, move to next kwarg type.
                        # If no transform is possible, format is unchanged and we rely on function to raise
                        # an Error.
                        continue
                    break

        # Anything that is still a Wrapper object, expand to native data format:
        for k, v in [(_k, _v) for _k, _v in kwargs.items() if isinstance(_v, Wrapper)]:
            try:
                kwargs[k] = v.data
            except Exception:
                pass

        # Extract args from kwargs:
        args = [kwargs.pop(name) for name in arg_names]
        return function(*args, **kwargs)

    @wraps(function)
    def wrapper(*args, _auto_inputs_transform=True, **kwargs):
        if not _auto_inputs_transform:  # Possibility to escape wrapping at call level
            return function(*args, **kwargs)
        return _wrapper(kwarg_types, convert_types, *args, **kwargs)

    return wrapper


def signature_mapping(signature, kwarg_types):
    """Map args and kwargs to object types, using hierarchical selection method:
    1. Explicitly defined type
    2. Based on Type setting in function
    3. Do nothing
    """
    mapping = {}
    for key, parameter in signature.parameters.items():
        if key in kwarg_types:
            # 1. Use explicitly defined type
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


def transform_module_inputs(in_module, **kwargs):
    """Transform the inputs to all functions in a module.

    Parameters
    ----------
    in_module : Module
        Module containing funcitons which are to be wrapped with transform_function_inputs
    kwarg_types : Dict[str: type]
        Mapping of accepted object types for each arg/kwarg
    convert_types : Tuple[type]
        List of data-types to try to convert, this can be useful when the function is versitile and can
        accept a large number of data-types, hence only a small number of types should be converted.
    kwargs: Any
        Any other kwargs accepted by transform_function_inputs

    Returns
    -------
    Module
        Version of in_module where all functions are wrapped with transform_modul_inputs
    """
    # wrapped_module must be different to original to prevent overriding cached module
    wrapped_module = types.ModuleType(__name__)
    for name in dir(in_module):
        func = getattr(in_module, name)
        # Wrap any functions that are not hidden
        if not name.startswith("_") and isinstance(func, types.FunctionType):
            setattr(
                wrapped_module,
                name,
                transform_function_inputs(func, **kwargs),
            )
        else:
            # If not a func, we just copy
            setattr(wrapped_module, name, func)

    return wrapped_module
