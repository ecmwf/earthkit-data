# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""
Import and check availability of optional dependencies
"""

from importlib import import_module


class ImporterItem:
    def __init__(self, module, message):
        self._status = None
        self._module = module
        self._message = message

        if not isinstance(self._module, tuple):
            self._module = (self._module,)

    def import_module(self):
        if self._status is not None and not self._status:
            raise ModuleNotFoundError(self._message)

        try:
            r = self._import()
            self._status = True
        except Exception as e:
            self._status = False
            raise type(e)(self._message + " ") from e

        return r

    def _import(self):
        if len(self._module) == 1:
            return import_module(self._module[0])
        else:
            for i, m in enumerate(self._module):
                if i < len(self._module) - 1:
                    try:
                        return import_module(m)
                    except Exception:
                        pass
                else:
                    return import_module(m)


class Importer:
    def __init__(self):
        self._conf = {}
        for k, v in _conf.items():
            self._conf[k] = ImporterItem(k, v)

    def import_module(self, module):
        k = module
        if isinstance(k, list):
            k = tuple(k)

        return self._conf[k].import_module()


_conf = {
    "cartopy.crs": "this feature requires 'cartopy' to be installed",
    "cdsapi": "the 'cds' and 'ads' sources require 'cdsapi' to be installed",
    ("codc", "pyodc"): "ODB data handling requires 'codc' or 'pyodc' to be installed!",
    "ecmwfapi": "the 'mars' source requires 'ecmwf-api-client' to be installed",
    "ecmwf.opendata": "the 'ecmwf-opendata' source requires 'ecmwf-opendata' to be installed",
    "geopandas": "this feature requires 'geopandas' to be installed!",
    "hda": "the 'wekeo' and 'wekeo-cds` sources require 'hda' to be installed",
    "polytope": "the 'polytope' source requires 'polytope-client' to be installed",
    "pdbufr": "BUFR data handling requires 'pdbufr' to be installed",
    "pyfdb": "the 'fdb' source requires 'pyfdb' to be installed",
}

IMPORTER = Importer()
