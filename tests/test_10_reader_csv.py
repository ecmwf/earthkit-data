import os

import emohawk

ROOT_DIR = os.path.dirname(emohawk.__path__[0])
# MULTI_CSV_ZIP_FILE = f"{ROOT_DIR}/notebooks/data/ERA5_t2m_UK_multi_csv.zip"
SINGLE_CSV_FILE = f"{ROOT_DIR}/notebooks/data/ERA5_t2m_UK_single_csv/t2m_UK_00:00.csv"
SINGLE_CSV_ZIP_FILE = f"{ROOT_DIR}/notebooks/data/ERA5_t2m_UK_single_csv.zip"

if not os.path.isfile(SINGLE_CSV_FILE):
    from zipfile import ZipFile

    with ZipFile(SINGLE_CSV_ZIP_FILE) as zf:
        zf.extractall(path=os.path.dirname(SINGLE_CSV_FILE))


def test_emohawk_open_csv():
    for filename in [
        SINGLE_CSV_ZIP_FILE,
        # NOT YET IMPLEMENTED:
        # MULTI_CSV_ZIP_FILE,
    ]:
        data = emohawk.open(filename)

        # check data can open as pandas dataframe:
        data.to_pandas()

        # check data can open as xarray
        data.to_xarray()
