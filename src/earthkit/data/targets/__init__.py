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
from functools import lru_cache
from importlib import import_module

LOG = logging.getLogger(__name__)


# _TARGETS = {}


class Target(metaclass=ABCMeta):
    """
    Represent a target.

    Parameters:
    -----------
    encoder: str, Encoder, None
        The encoder to use to encode the data. Can be overridden in the the :obj:`write` method.
        When a string is passed, the encoder is looked up in the available encoders. When None,
        the encoder will be determined from the data to write (if possible) or from the :class:`Target` properties.
    template: obj, None
        The template to use to encode the data. Can be overridden in the :obj:`write` method.

    The :class:`Target` is used to write data to a specific location. The target can be
    a file, a database, a remote server, etc.

    :class:`Target` is an abstract class and should not be used directly. Instead, use one
    of the concrete implementations.
    """

    def __init__(self, encoder=None, template=None):
        self._encoder = encoder
        self._template = template

    def write(
        self,
        data=None,
        encoder=None,
        template=None,
        metadata=None,
        **kwargs,
    ):
        """
        Write data to the target using the given encoder.

        Parameters:
        -----------
        data: obj, None
            The data object to write. If None, the encoder will use all the other arguments
            to generate the data to write.
        encoder: str, Encoder, None
            The encoder to use to encode the data.
            When a string is passed, the encoder is looked up in the available encoders. When None,
            the encoder the :class:`Target` was created with will be used if available. Otherwise, the encoder will be determined from the data to write (if possible) or from the :class:`Target` properties.
        template: obj, None
            The template to use to encode the data. When None,
            the template the :class:`Target` was created with will be used if available.
        metadata: dict, None
            Metadata to pass to the encoder.
        **kwargs: dict
            Other keyword arguments passed to the encoder.
        """
        if data is not None:
            data._to_target(self, encoder=encoder, template=template, metadata=metadata, **kwargs)
        else:
            self._write_data(None, encoder=encoder, template=template, metadata=metadata, **kwargs)

    @abstractmethod
    def _write_data(
        self,
        data,
        **kwargs,
    ):
        pass

    @abstractmethod
    def _write_reader(self, reader, **kwargs):
        """Write a Reader to the target.

        Parameters:
        -----------
        reader: :obj:`Reader`
            The Reader whose data is written to the target.
        """
        pass

    @abstractmethod
    def _write_field(self, field, **kwargs):
        """Write a Field to the target.

        Parameters:
        -----------
        field: :obj:`Field`
            The field to write to the target.
        """
        pass

    @abstractmethod
    def _write_fieldlist(self, fieldlist, **kwargs):
        """Write a FieldList to the target.

        Parameters:
        -----------
        field: :obj:`FieldList`
            The fieldlist to write to the target.
        """
        pass

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def encode(self, data, encoder=None, default_encoder=None, template=None, suffix=None, **kwargs):
        from earthkit.data.encoders import _find_encoder

        if encoder is None:
            encoder = self._encoder
        encoder = _find_encoder(data, encoder, default_encoder=default_encoder, suffix=suffix)

        if template is None:
            template = self._template

        return encoder.encode(data, template=template, **kwargs)


class TargetLoader:
    kind = "target"

    def load_module(self, module):
        return import_module(module, package=__name__).target

    def load_entry(self, entry):
        entry = entry.load()
        if callable(entry):
            return entry
        return entry.target

    def load_remote(self, name):
        return None


class TargetMaker:
    TARGETS = {}

    def __call__(self, name, *args, **kwargs):
        loader = TargetLoader()

        if name in self.TARGETS:
            klass = self.TARGETS[name]
        else:
            from earthkit.data.core.plugins import find_plugin

            klass = find_plugin(os.path.dirname(__file__), name, loader)
            self.TARGETS[name] = klass

        target = klass(*args, **kwargs)

        if getattr(target, "name", None) is None:
            target.name = name

        return target

    def __getattr__(self, name):
        return self(name.replace("_", "-"))


get_target = TargetMaker()


def make_target(name, *args, **kwargs):
    return get_target(name, *args, **kwargs)

    # target = _targets().get(name, None)
    # if target is None:
    #     raise ValueError(f"Unknown target {name}")

    # return target(*args, **kwargs)


def ensure_target(target_or_name, *args, **kwargs):
    if isinstance(target_or_name, Target):
        return target_or_name
    target = make_target(target_or_name, *args, **kwargs)
    return target


@lru_cache
def target_kwargs(target_type):
    import inspect

    r = inspect.signature(target_type.__init__)
    v = []
    for p in r.parameters.values():
        if p.kind == p.KEYWORD_ONLY or p.kind == (p.POSITIONAL_OR_KEYWORD and p.default is not p.empty):
            v.append(p.name)
    return v


def to_target(target, *args, **kwargs):
    if not isinstance(target, str):
        raise ValueError(f"Invalid target {target}. Must be a string")

    with ensure_target(target, *args, **kwargs) as t:
        for k in target_kwargs(type(target)) + target_kwargs(Target):
            kwargs.pop(k, None)

        t.write(**kwargs)


# @locked
# def _targets():
#     if not _TARGETS:
#         here = os.path.dirname(__file__)
#         for path in sorted(os.listdir(here)):
#             if path[0] in ("_", "."):
#                 continue

#             if path.endswith(".py") or os.path.isdir(os.path.join(here, path)):
#                 name, _ = os.path.splitext(path)
#                 try:
#                     module = import_module(f".{name}", package=__name__)
#                     if hasattr(module, "target"):
#                         w = getattr(module, "target")
#                         # _TARGETS[w.DATA_FORMAT] = w
#                         _TARGETS[name] = w
#                 except Exception:
#                     LOG.exception("Error loading writer %s", name)

#     return _TARGETS
