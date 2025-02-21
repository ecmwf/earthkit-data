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


class Target(metaclass=ABCMeta):
    """
    Represent a target.

    Parameters:
    -----------
    encoder: str, Encoder, None
        The encoder to use to encode the data. Can be overridden in the the :obj:`write` method.
        When a string is passed, the encoder is looked up in the available encoders. When None,
        the encoder will be determined from the data to write (if possible) or from
        the :class:`Target` properties.
    template: obj, None
        The template to use to encode the data. Can be overridden in the :obj:`write` method.
    metadata: dict, None
        Metadata to pass to the encoder.

    The :class:`Target` is used to write data to a specific location. The target can be
    a file, a database, a remote server, etc.
    """

    def __init__(self, encoder=None, template=None, metadata=None, **kwargs):
        self._encoder = encoder
        self._template = template
        self._metadata = metadata or {}
        self._closed = False

    @abstractmethod
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
            the encoder the :class:`Target` was created with will be used if available. Otherwise,
            the encoder will be determined from the data to write (if possible) or from
            the :class:`Target` properties.
        template: obj, None
            The template to use to encode the data. When None,
            the template the :class:`Target` was created with will be used if available.
        metadata: dict, None
            Metadata to pass to the encoder.
        **kwargs: dict
            Other keyword arguments passed to the encoder.

        Raises:
        -------
        ValueError: If the target is already closed.
        """
        pass

    @abstractmethod
    def close(self):
        """Close the target.

        The implementation must close the target and release any resources.
        It must also call :obj:`_mark_closed`. The target will not be able
        to write anymore.

        Raises:
        -------
        ValueError: If the target is already closed.
        """
        pass

    @abstractmethod
    def flush(self):
        """Flush the target.

        Some targets may require to flush the data to the underlying storage.

        Raises:
        -------
        ValueError: If the target is already closed.
        """
        pass

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @property
    def closed(self):
        """True if the target is closed, False otherwise."""
        return self._closed

    def _mark_closed(self):
        """Register the target as closed."""
        self._raise_if_closed()
        self._closed = True

    def _raise_if_closed(self):
        """Raise an error if the target is closed."""
        if self.closed:
            raise ValueError("Target is closed")


class SimpleTarget(Target):
    def write(
        self,
        data=None,
        **kwargs,
    ):
        self._raise_if_closed()

        if data is not None:
            if hasattr(data, "sources"):
                for d in data.sources:
                    self.write(d, **kwargs)
            elif hasattr(data, "to_target"):
                self._write(data, **kwargs)
            # elif "values" not in kwargs:
            #     # TODO: this should be reviewed
            #     self._write(None, values=data, **kwargs)
            else:
                raise ValueError("Cannot write data to target")
        else:
            self._write(None, **kwargs)

    @abstractmethod
    def _write(self, data, **kwargs):
        """Write generic data to the target.

        Parameters:
        -----------
        data:
            Data to write to the target.
        """
        pass

    def _encode(self, data, encoder=None, template=None, suffix=None, **kwargs):
        """Helper method to encode data.

        Returns
        -------
        :class:`EncodedData`
            The encoded data.
        """
        from earthkit.data.encoders import make_encoder

        if encoder is None:
            encoder = self._encoder

        encoder = make_encoder(data, encoder, suffix=suffix, metadata=self._metadata)

        if template is None:
            template = self._template

        return encoder.encode(data, template=template, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


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

    def __call__(self, name_or_target, *args, **kwargs):
        if isinstance(name_or_target, Target):
            return name_or_target

        name = name_or_target

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


create_target = TargetMaker()


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
    """Write data to a target.

    This is a top level function that writes data to a target.

    Parameters:
    -----------
    target: str
        The target to write to. Must be a string.
    """

    # data = kwargs.pop("data", None)

    with create_target(target, *args, **kwargs) as t:
        for k in [*target_kwargs(type(t)), *target_kwargs(Target)]:
            kwargs.pop(k, None)

        t.write(**kwargs)
