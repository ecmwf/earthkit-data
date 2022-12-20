import os

import emohawk

ROOT_DIR = os.path.dirname(emohawk.__path__[0])
SINGLE_NETCDF_ZIP_FILE = f"{ROOT_DIR}/notebooks/data/ERA5_t2m_UK_single_netcdf.zip"
MULTI_NETCDF_ZIP_FILE = f"{ROOT_DIR}/notebooks/data/ERA5_t2m_UK_multi_netcdf.zip"
MIXED_MULTI_NETCDF_ZIP_FILE = (
    f"{ROOT_DIR}/notebooks/data/ERA5_UK_mixed_multi_netcdf.zip"
)
SINGLE_GRIB_ZIP_FILE = f"{ROOT_DIR}/notebooks/data/ERA5_t2m_UK_single_grib.zip"
MULTI_CSV_ZIP_FILE = f"{ROOT_DIR}/notebooks/data/ERA5_t2m_UK_multi_csv.zip"
SINGLE_CSV_ZIP_FILE = f"{ROOT_DIR}/notebooks/data/ERA5_t2m_UK_single_csv.zip"
MULTI_GRIB_ZIP_FILE = f"{ROOT_DIR}/notebooks/data/ERA5_t2m_UK_multi_grib.zip"


def test_emohawk_open_zip():
    for filename in [
        SINGLE_NETCDF_ZIP_FILE,
        MULTI_NETCDF_ZIP_FILE,
        MIXED_MULTI_NETCDF_ZIP_FILE,
        SINGLE_CSV_ZIP_FILE,
        # NOT YET IMPLEMENTED:
        # MULTI_CSV_ZIP_FILE,
        # SINGLE_GRIB_ZIP_FILE,
        # MULTI_GRIB_ZIP_FILE,
    ]:
        emohawk.open(filename)
