"""
Module containing methods to transform the inputs of functions based on the function type setting,
common signitures or mapping defined at call time
"""
from ast import Module
import inspect
import types
import typing as T
from functools import wraps

from earthkit.data import transform

try:
    UNION_TYPES = [T.Union, types.UnionType]
except AttributeError:
    # types.UnionType is not in versions of python<3.9
    UNION_TYPES = [
        T.Union,
    ]

EMPTY_TYPES = [inspect._empty]


def ensure_iterable(input_item):
    """Ensure that an item is iterable"""
    if not isinstance(input_item, (tuple, list, dict)):
        return [input_item]
    return input_item


def transform_function_inputs(function, **kwarg_types):
    """
    Transform the inputs to a function to match the requirements.
    earthkit.data handles the input arg/kwarg format.
    """
    def _wrapper(kwarg_types, *args, **kwargs):
        kwarg_types = {**kwarg_types}
        signature = inspect.signature(function)
        mapping = signature_mapping(signature, kwarg_types)

        # convert args to kwargs for ease of looping:
        for arg, name in zip(args, signature.parameters):
            kwargs[name] = arg

        kwargs_with_mapping = [k for k in kwargs if k in mapping]
        # transform args/kwargs if mapping available
        for key in kwargs_with_mapping:
            value = kwargs[key]
            kwarg_types = ensure_iterable(mapping[key])
            # Transform value if necessary
            if type(value) not in kwarg_types:
                for kwarg_type in kwarg_types:
                    try:
                        kwargs[key] = transform(value, kwarg_type)
                    except ValueError:
                        # Transform was not possible, move to next kwarg type.
                        # If no transform is possible, format is unchanged and we rely on function to raise
                        # an Error.
                        continue
                    break

        return function(**kwargs)

    @wraps(function)
    def wrapper(*args, **kwargs):
        return _wrapper(kwarg_types, *args, **kwargs)

    return wrapper


def signature_mapping(signature, kwarg_types):
    """
    Map args and kwargs to object types, using hierarchical selection method:
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


def transform_module_inputs(in_module, **decorator_kwargs):
    """
    Transform the inputs to all functions in a module.
    """
    # wrapped_module must be different to original to prevent overriding cached module
    wrapped_module = Module
    for name in dir(in_module):
        func = getattr(in_module, name)
        # Wrap any functions that are not hidden
        if not name.startswith('_') and isinstance(func, types.FunctionType):
            setattr(wrapped_module, name, transform_function_inputs(func, **decorator_kwargs))
        else:
            # If not a func, we just copy
            setattr(wrapped_module, name, func)
    return wrapped_module
