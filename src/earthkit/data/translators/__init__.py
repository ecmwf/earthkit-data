import logging
import os

import earthkit.data as data
from earthkit.data.core import Base
from earthkit.data.decorators import locked
from earthkit.data.wrappers import _helpers

LOG = logging.getLogger(__name__)


class Translator(Base):
    def __call__(self):
        """
        Return unmodified data.
        """
        return self.data


_TRANSLATORS = {}


@locked
def _translators():
    return _helpers("translator", _TRANSLATORS, here=os.path.dirname(__file__), package=__name__)


def get_translator(source, cls, *args, **kwargs):
    """Get the appropriate translator for the source based on the target cls."""
    if not isinstance(source, Base):
        source = data.from_object(source)

    for name, h in _translators().items():
        translator = h(source, cls, *args, **kwargs)
        if translator is not None:
            return translator

    raise ValueError(f"Cannot find a translator for class {cls.__name__}")


def transform(*args, **kwargs):
    """Executing wrapper for the get_translator class method"""
    return get_translator(*args, **kwargs)()
