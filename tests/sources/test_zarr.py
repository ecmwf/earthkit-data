import pytest

from earthkit.data.readers.netcdf.field import XArrayField
from earthkit.data import from_source
from earthkit.data.testing import earthkit_test_data_file

@pytest.mark.no_eccodes
def test_zarr_source():
    ds = from_source("zarr", earthkit_test_data_file("test_zarr/"))
    assert len(ds) == 4
    assert isinstance(ds[0], XArrayField)
    assert isinstance(ds[1], XArrayField)
    assert isinstance(ds[2], XArrayField)
    assert isinstance(ds[3], XArrayField)