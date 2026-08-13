# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import importlib


def _register(ekm_module_name, ekd_module, method_names):
    """Register array computation methods from the earthkit-meteo module or the local module."""
    res = []
    found = set()
    try:
        module = importlib.import_module(f"earthkit.meteo.{ekm_module_name}.array")
        for method_name in method_names:
            if hasattr(module, method_name):
                res.append(getattr(module, method_name))
                found.add(method_name)
    except ImportError:
        pass

    for method_name in method_names:
        if method_name not in found:
            try:
                res.append(getattr(ekd_module, method_name))
            except AttributeError:
                pass

    return res
