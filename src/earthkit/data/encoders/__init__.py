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
import re
from abc import ABCMeta
from abc import abstractmethod
from importlib import import_module

from earthkit.data.decorators import locked

LOG = logging.getLogger(__name__)

_ENCODERS = {}


class DataPresenter:
    def __init__(self, data):
        self.data = data

    def to_bytes(self, data):
        return data

    def to_file(self, target):
        self.data.write(target.f)


class Encoder(metaclass=ABCMeta):
    def __init__(self, template=None, metadata=None, **kwargs):
        self.template = template
        self.metadata = metadata or {}
        self.kwargs = kwargs

    @abstractmethod
    def encode(
        self,
        data=None,
        values=None,
        check_nans=False,
        metadata={},
        template=None,
        # return_bytes=False,
        missing_value=9999,
        **kwargs,
    ):
        pass


class DefaultEncoder(Encoder):
    def encode(self, data=None, **kwargs):
        if data is None:
            raise ValueError("No data to encode")
        return data


@locked
def _encoders():
    if not _ENCODERS:
        here = os.path.dirname(__file__)
        for path in sorted(os.listdir(here)):
            if path[0] in ("_", "."):
                continue

            if path.endswith(".py") or os.path.isdir(os.path.join(here, path)):
                name, _ = os.path.splitext(path)
                try:
                    module = import_module(f".{name}", package=__name__)
                    if hasattr(module, "Encoder"):
                        w = getattr(module, "Encoder")
                        # _ENCODERS[w.DATA_FORMAT] = w
                        _ENCODERS[name] = w
                except Exception as e:
                    LOG.exception("Error loading encoder %s", name)

    return _ENCODERS


def _get_encoder(name, data_format=None):
    if data_format is not None:
        combined_name = f"{data_format}_to_{name}"
        r = _encoders().get(combined_name, None)
        if r:
            return r
    # print(f"{name=}, {data_format=}")
    r = _encoders().get(name, None)
    if r is None:
        raise ValueError(f"Unknown encoder {name=} {data_format=}")
    return r


def _find_encoder(data, encoder=None, **kwargs):
    # if data_format is not None and not isinstance(data_format, str):
    #     raise ValueError(f"data_format must be a str or None, got {data_format=}")

    # print(f"_encoders()={_encoders()}")

    if not isinstance(encoder, Encoder):
        data_format = None
        if data is not None:
            if hasattr(data, "metadata"):
                data_format = data.metadata().data_format()
                if data_format:
                    if encoder is None:
                        encoder = data_format
                        data_format = None
                    elif encoder == data_format:
                        data_format = None
        elif encoder is None:
            raise ValueError("No data or encoder")

        # print(f"{data=}, {encoder=}, {data_format=}")

        if encoder is None:
            raise ValueError(f"Could not create encoder for {data=}, {encoder=}")
        if not isinstance(encoder, str):
            raise ValueError(f"Unsupported encoder={encoder}. Must be a str or Encoder")

        encoder = _get_encoder(encoder, data_format=data_format)
        assert encoder is not None
        # print("ENCODER kwargs", kwargs)
        encoder = encoder(**kwargs)

    # if encoder is None:
    #     encoder = DefaultEncoder()

    if isinstance(encoder, Encoder):
        return encoder
