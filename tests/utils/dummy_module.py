
import numpy as np
import xarray as xr

dummy_attribute_1 = 1
dummy_attribute_2 = 2

XR_TYPES = (xr.Dataset, xr.DataArray, xr.Variable)

def numpy_mean(
    a: np.ndarray,
    **kwargs
):
    return np.mean(a, **kwargs)

def xarray_ones_like(
    dataarray: xr.DataArray,
    **kwargs
):
    return xr.ones_like(dataarray, **kwargs)
