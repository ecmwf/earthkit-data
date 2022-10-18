# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import os
import warnings
from importlib import import_module

from emohawk import Data


class Reader(Data):

    BINARY = True

    def mutate(self):
        # Give a chance to `directory` or `zip` to change the reader
        return self

    def mutate_source(self):
        # The source may ask if it needs to mutate
        return None

    def sel(self, *args, **kwargs):
        raise NotImplementedError()

    def save(self, path):
        mode = "wb" if self.BINARY else "w"
        with open(path, mode) as f:
            self.write(f)

    def write(self, f):
        mode = "rb" if self.BINARY else "r"
        with open(self.source, mode) as g:
            while True:
                chunk = g.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)


_READERS = {}


def _readers():
    if not _READERS:
        here = os.path.dirname(__file__)
        for path in sorted(os.listdir(here)):

            if path[0] in ("_", "."):
                continue

            if path.endswith(".py") or os.path.isdir(os.path.join(here, path)):

                name, _ = os.path.splitext(path)

                try:
                    module = import_module(f".{name}", package=__name__)
                    if hasattr(module, "reader"):
                        _READERS[name] = module.reader
                        if hasattr(module, "aliases"):
                            for a in module.aliases:
                                assert a not in _READERS
                                _READERS[a] = module.reader
                except Exception:
                    warnings.warn(f"Error loading reader {name}")

    return _READERS


def get_reader(path, *args, **kwargs):

    if os.path.isdir(path):
        magic = None
    else:
        with open(path, "rb") as f:
            magic = f.read(8)

    for deeper_check in (False, True):
        # We do two passes, the second one
        # allow the plugin to look deeper in the file
        for name, r in _readers().items():
            reader = r(path, magic, deeper_check)
            if reader is not None:
                return reader.mutate()

    raise TypeError(f"Could not open file {path}")
