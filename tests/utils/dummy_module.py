import typing as T

import numpy as np
import pandas as pd
import xarray as xr

dummy_attribute_1 = 1
dummy_attribute_2 = 2

XR_TYPES = (xr.Dataset, xr.DataArray, xr.Variable)


def numpy_mean(
    a: T.Union[np.ndarray, xr.Dataset, xr.DataArray, xr.Variable, pd.DataFrame, pd.Series],
    **kwargs,
):
    return np.mean(a, **kwargs)


def xarray_ones_like(dataarray: T.Union[xr.DataArray, xr.Dataset], **kwargs):
    return xr.ones_like(dataarray, **kwargs)
