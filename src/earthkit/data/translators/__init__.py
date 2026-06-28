# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
#

import logging
import os
from abc import abstractmethod

from earthkit.data.core import Base
from earthkit.data.data.wrappers import _helpers
from earthkit.data.decorators import locked

LOG = logging.getLogger(__name__)


class Translator(Base):
    _name = None

    def __init__(self, data, *args, **kwargs):
        self._data = data

    @abstractmethod
    def __call__(self):
        pass


_TRANSLATORS = {}


@locked
def _translators():
    return _helpers("translator", _TRANSLATORS, here=os.path.dirname(__file__), package=__name__)


def get_translator(source, cls, *args, **kwargs):
    """Get the appropriate translator for the source based on the target cls."""
    if not isinstance(source, Base):
        from earthkit.data import from_object

        source = from_object(source)

    for _, klass in _translators().items():
        translator = klass(source, cls, *args, **kwargs)
        if translator is not None:
            return translator

    raise ValueError(f"Cannot find a translator for class {cls.__name__}")


def transform(*args, **kwargs):
    """Executing wrapper for the get_translator class method."""
    return get_translator(*args, **kwargs)()
