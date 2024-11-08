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
from abc import ABCMeta
from abc import abstractmethod
from importlib import import_module

from earthkit.data.decorators import locked

LOG = logging.getLogger(__name__)


_TARGETS = {}


class Target(metaclass=ABCMeta):
    @abstractmethod
    def write(
        self,
        *args,
        **kwargs,
    ):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return


# def find_target(name):
#     if name == "file":
#         return FileTarget()


def write(f, field, **kwargs):
    x = _targets(field._metadata.data_format())
    c = x()
    c.write(f, field, **kwargs)


def make_target(name, *args, **kwargs):
    target = _targets().get(name, None)
    if target is None:
        raise ValueError(f"Unknown target {name}")

    return target(*args, **kwargs)


def to_target(name, *args, **kwargs):
    target = make_target(name, *args, **kwargs)
    target.write(**kwargs)


@locked
def _targets():
    if not _TARGETS:
        here = os.path.dirname(__file__)
        for path in sorted(os.listdir(here)):
            if path[0] in ("_", "."):
                continue

            if path.endswith(".py") or os.path.isdir(os.path.join(here, path)):
                name, _ = os.path.splitext(path)
                try:
                    module = import_module(f".{name}", package=__name__)
                    if hasattr(module, "Target"):
                        w = getattr(module, "Target")
                        # _TARGETS[w.DATA_FORMAT] = w
                        _TARGETS[name] = w
                except Exception:
                    LOG.exception("Error loading writer %s", name)

    return _TARGETS


# import logging
# import os
# from abc import ABCMeta
# from abc import abstractmethod
# from importlib import import_module

# from earthkit.data.decorators import locked

# LOG = logging.getLogger(__name__)


# _WRITERS = {}


# class Writer(metaclass=ABCMeta):
#     @abstractmethod
#     def write(self, f, values, metadata, **kwargs):
#         pass


# def write(f, field, **kwargs):
#     x = _writers(field._metadata.data_format())
#     c = x()
#     c.write(f, field, **kwargs)


# @locked
# def _writers(method_name):
#     if not _WRITERS:
#         here = os.path.dirname(__file__)
#         for path in sorted(os.listdir(here)):
#             if path[0] in ("_", "."):
#                 continue

#             if path.endswith(".py") or os.path.isdir(os.path.join(here, path)):
#                 name, _ = os.path.splitext(path)
#                 try:
#                     module = import_module(f".{name}", package=__name__)
#                     if hasattr(module, "Writer"):
#                         w = getattr(module, "Writer")
#                         _WRITERS[w.DATA_FORMAT] = w
#                         _WRITERS[name] = w
#                 except Exception:
#                     LOG.exception("Error loading writer %s", name)

#     return _WRITERS[method_name]
