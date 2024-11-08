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
from io import IOBase
from types import UnionType

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


class Encoder:
    def __init__(self, template=None, **kwargs):
        pass

    def encode(
        self,
        data,
        values=None,
        check_nans=False,
        metadata={},
        template=None,
        return_bytes=False,
        missing_value=9999,
        **kwargs,
    ):
        pass


class DefaultEncoder(Encoder):
    def encode(self, data, **kwargs):
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
                except Exception:
                    LOG.exception("Error loading encoder %s", name)

    return _ENCODERS


def _find_encoder(data, encoder=None, data_format=None, **kwargs):
    if data_format is not None and not isinstance(data_format, str):
        raise ValueError(f"data_format must be a str or None, got {data_format=}")

    if encoder is None and isinstance(data_format, str):
        encoder = data_format

    if hasattr(data, "metadata"):
        encoder = data.metadata().data_format()

    if isinstance(encoder, str):
        if encoder not in _encoders():
            raise ValueError(f"Unknown encoder={encoder}")
        encoder = _encoders()[encoder](data, **kwargs)

    if encoder is None:
        encoder = DefaultEncoder()

    if isinstance(encoder, Encoder):
        return encoder
