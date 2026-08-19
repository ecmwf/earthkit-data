# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import importlib


def _resolve(ekm_module_name, ekd_module, method_names):
    """Resolve array computation methods from earthkit-meteo, falling back to the local module.

    Parameters
    ----------
    ekm_module_name: str
        Name of the earthkit-meteo subpackage to resolve the methods from. The methods are
        looked up in ``earthkit.meteo.{ekm_module_name}.array``.
    ekd_module: module
        The local module providing the fallback implementations.
    method_names: iterable of str
        The names of the methods to resolve.

    Returns
    -------
    dict of str to callable
        The resolved methods, keyed by the name they were requested under.

    Raises
    ------
    AttributeError
        If a method is available neither in earthkit-meteo nor in ``ekd_module``.
    """
    try:
        ekm_module = importlib.import_module(f"earthkit.meteo.{ekm_module_name}.array")
    except ImportError:
        ekm_module = None

    res = {}
    for name in method_names:
        for module in (ekm_module, ekd_module):
            method = getattr(module, name, None)
            if callable(method):
                res[name] = method
                break
        else:
            raise AttributeError(
                f"Method '{name}' is available neither in "
                f"'earthkit.meteo.{ekm_module_name}.array' nor in '{ekd_module.__name__}'"
            )

    return res
