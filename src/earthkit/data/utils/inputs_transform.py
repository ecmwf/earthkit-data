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
from earthkit.data.wrappers import call_wrapper_method

LOG = logging.getLogger(__name__)

try:
    UNION_TYPES = [T.Union, types.UnionType]
except AttributeError:
    # types.UnionType is not in versions of python<3.9
    UNION_TYPES = [
        T.Union,
    ]

EMPTY_TYPES = [inspect._empty]

PARAMETER_METADATA_MODELS = {
    "test": {
        "var1": {
            "units": {"K"},
            "standard_name": {"air_temperature"},
        }
    }
}

DEFAULT_PARAMETER_METADATA_MODEL = "test"


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


def create_provenance_metadata(
    function: T.Callable,
    *args,
    **kwargs,
):
    """Create provenance metadata for a function call.

    Parameters
    ----------
    function : Callable
        The function for which to create provenance metadata.
    extra_provenance : Dict[str, str or Dict[str, str]]
        Additional provenance metadata to include. This can be used to add
        information that is not automatically captured by this function.
        It will supercede any provenance metadata created automatically.
    *args : Any
        Positional arguments passed to the function.
    **kwargs : Any
        Keyword arguments passed to the function.

    Returns
    -------
    Dict
        A dictionary containing provenance metadata.
    """
    provenance_metadata = {}

    signature = inspect.signature(function)
    bound_args = signature.bind_partial(*args, **kwargs)
    bound_args.apply_defaults()
    parameters = {
        k: type(v) for k, v in dict(bound_args.arguments).items()
    }

    provenance_metadata["call_info"] = {
        "module": getattr(function, "__module__", None),
        "function": getattr(function, "__name__", None),
        "parameters": parameters,
    }

    return provenance_metadata


def metadata_handler(
    output_metadata: dict[str, str] | None = None,
    provenance: bool | T.Callable = False,
    extra_provenance: dict[str, str | dict[str, str]] | None = None,
    parameter_metadata_model: str | dict[str, T.Any] | None = DEFAULT_PARAMETER_METADATA_MODEL,
    parameter_mapping: dict[str, str] | None = None,
    ensure_units: T.Union[None, T.Dict[str, str]] = None,
):
    """Decorator to ensure units on function arguments.

    Parameters
    ----------
    ensure_units : Dict[str, str]
        Ensure that the given arguments have the specified units, provided as {arg_name: target_units}.
    provenance : bool | Callable
        Whether to add provenance information to the output data. The end user should be able to set this
        option. If a callable is provided, it will be used to generate the provenance metadata. The
        function should have the signature: func(function: Callable, args: list, kwargs: dict).
    parameter_metadata_model : str or Dict[str, Any]
        Metadata model to use for validating and updating parameter metadata. If a string is provided,
        it should correspond to a key in the `PARAMETER_METADATA_MODELS` dictionary. If a dictionary is
        provided, it will be used directly as the metadata model.
    parameter_mapping : Dict[str, str]
        Mapping of argument names to keys in the parameter metadata model,
        to be used for validation and updating metadata.

    Returns
    -------
    Callable
        Wrapped function.
    """

    def decorator(function: T.Callable) -> T.Callable:
        def _wrapper(
            *args,
            output_metadata: dict[str, str] | None = output_metadata,
            provenance: bool | T.Callable = provenance,
            parameter_metadata_model: str | dict[str, T.Any] | None = parameter_metadata_model,
            source_units: T.Dict[str, str] | None = None,
            ensure_units: T.Union[None, T.Dict[str, str]] = ensure_units,
            parameter_mapping: dict[str, str] | None = parameter_mapping,
            **kwargs,
        ):

            signature = inspect.signature(function)

            # Store positional arg names for extraction later
            arg_names = []
            for arg, name in zip(args, signature.parameters):
                arg_names.append(name)
                kwargs[name] = arg

            provenance_metadata: dict[str, T.Any] = {}

            # Validate against metadata model
            if parameter_metadata_model is None:
                parameter_metadata_model = {}
            elif isinstance(parameter_metadata_model, str):
                parameter_metadata_model = PARAMETER_METADATA_MODELS.get(parameter_metadata_model, {})

            # TODO: This has the potential to overwrite existing metadata keys
            #  Also unnecessary if parameter_metadata_model is empty
            if parameter_mapping is None:
                parameter_mapping = {}
            for key, value in parameter_mapping.items():
                if value in parameter_metadata_model:
                    parameter_metadata_model[key] = parameter_metadata_model[value]

            # Ensure units
            if ensure_units is None:
                # If ensure_units not provided, guess from metadata model
                ensure_units = {
                    k: v["units"] for k, v in (parameter_metadata_model or {}).items() if "units" in v
                }

            print(0, provenance_metadata)
            for key in kwargs.keys() & ensure_units.keys():
                kwargs[key] = call_wrapper_method(
                    kwargs[key],
                    "convert_units",
                    target_units=ensure_units[key],
                    source_units=source_units.get(key) if source_units else None,
                    provenance_metadata=provenance_metadata,
                )
            print(1, provenance_metadata)

            for key in kwargs.keys() & parameter_metadata_model.keys():
                kwargs[key] = call_wrapper_method(
                    kwargs[key],
                    "validate_parameter_metadata",
                    metadata_model=parameter_metadata_model[key],
                )

            args = [kwargs.pop(name) for name in arg_names]
            result = function(*args, **kwargs)

            if provenance is True:
                provenance_generator = create_provenance_metadata
            elif callable(provenance):
                provenance_generator = provenance
            else:
                provenance_generator = None
            if provenance_generator is not None:
                provenance_metadata.update(provenance_generator(function, *args, **kwargs))
            provenance_metadata.update(extra_provenance or {})

            if not provenance:
                # Clear provenance metadata if not requested
                provenance_metadata = {}

            if output_metadata is None:
                output_metadata = {}

            result = call_wrapper_method(
                result,
                "update_metadata",
                earthkit_metadata=provenance_metadata,
                **output_metadata,
            )

            return result

        @wraps(function)
        def wrapper(*args, _auto_metadata_handler=True, **kwargs):
            if not _auto_metadata_handler:
                return function(*args, **kwargs)
            return _wrapper(*args, **kwargs)

        return wrapper

    return decorator


def format_handler(
    kwarg_types: T.Dict[str, T.Any] = {},
    convert_types: T.Union[None, T.Tuple[T.Any], T.Dict[str, T.Tuple[T.Any]]] = None,
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
                arg_names.append(name)
                kwargs[name] = arg

            # # Split args into multiple
            # if len(args) < len(expected_args):

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

            # TODO: Check if this is still needed
            # Expand Wrapper objects
            for k, v in list(kwargs.items()):
                if isinstance(v, Wrapper):
                    try:
                        kwargs[k] = v.data
                    except Exception:
                        pass

            # Extract positional args again
            args = [kwargs.pop(name) for name in arg_names]
            return function(*args, **kwargs)

        @wraps(function)
        def wrapper(*args, _auto_inputs_transform=True, **kwargs):
            if not _auto_inputs_transform:
                return function(*args, **kwargs)
            return _wrapper(kwarg_types, convert_types, *args, **kwargs)

        return wrapper

    return decorator


def signature_mapping(signature: inspect.Signature, kwarg_types: dict[str, str]):
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
