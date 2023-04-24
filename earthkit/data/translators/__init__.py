from earthkit.data.core import Base


def numpy_translator(source, cls):
    import numpy as np

    if cls in (np.ndarray,):
        return source.to_numpy

    return None


def pandas_translator(source, cls):
    import pandas as pd

    if cls in (pd.DataFrame,):
        return source.to_pandas

    return None


def xarray_translator(source, cls):
    """
    Translate an Earthkit object to xarray, if cls is xarray
    """
    import xarray as xr

    if cls in (xr.DataArray, xr.Dataset):
        return source.to_xarray

    return None


translators = {
    "numpy": numpy_translator,
    "pandas": pandas_translator,
    "xarray": xarray_translator,
}


def get_translator(source, cls):
    if not isinstance(source, Base):
        source = data.from_obj(source)

    for name, h in translators.items():
        translator = h(source, cls)
        if translator is not None:
            return translator()

    raise ValueError(f"Cannot find a translator for class {cls.__name__}")
