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
    return _helpers(
        "translator", _TRANSLATORS, here=os.path.dirname(__file__), package=__name__
    )


def get_translator(source, cls, *args, **kwargs):
    if not isinstance(source, Base):
        source = data.from_object(source)
    for name, h in _translators().items():
        translator = h(source, cls, *args, **kwargs)
        if translator is not None:
            print(translator)
            return translator()

    raise ValueError(f"Cannot find a translator for class {cls.__name__}")


# def numpy_translator(source, cls):
#     import numpy as np

#     if cls in (np.ndarray,):
#         return source.to_numpy

#     return None


# def pandas_translator(source, cls):
#     import pandas as pd

#     if cls in (pd.DataFrame,):
#         return source.to_pandas

#     return None


# def xarray_translator(source, cls):
#     """
#     Translate an Earthkit object to xarray, if cls is xarray
#     """
#     import xarray as xr

#     if cls in (xr.DataArray, xr.Dataset):
#         return source.to_xarray

#     return None


# translators = {
#     "numpy": numpy_translator,
#     "pandas": pandas_translator,
#     "xarray": xarray_translator,
# }
