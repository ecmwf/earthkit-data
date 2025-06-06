import importlib.util

import pytest

from earthkit.data import from_source
from earthkit.data.readers.netcdf.field import XArrayField
from earthkit.data.testing import earthkit_test_data_file

if importlib.util.find_spec("zarr") is not None:
    NO_ZARR = False
else:
    NO_ZARR = True


@pytest.mark.skipif(NO_ZARR, reason="Zarr not installed")
def test_zarr_source():
    ds = from_source("xarray-zarr", earthkit_test_data_file("test_zarr/"))
    assert len(ds) == 4
    assert isinstance(ds[0], XArrayField)
    assert isinstance(ds[1], XArrayField)
    assert isinstance(ds[2], XArrayField)
    assert isinstance(ds[3], XArrayField)
