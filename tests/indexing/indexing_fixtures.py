#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import shutil

from earthkit.data.core.temporary import temp_directory, temp_file
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file

# TEST_GRIB_FILES = [
#     earthkit_file(p)
#     for p in [
#         "docs/examples/test.grib",
#         "docs/examples/test4.grib",
#     ]
# ]


def unique_grib_file():
    tmp = temp_file()
    shutil.copy(earthkit_examples_file("tuv_pl.grib"), tmp.path)
    return tmp


def unique_grib_file_list():
    tmp = []
    for p in ["t", "u", "v"]:
        f = temp_file()
        shutil.copy(earthkit_test_data_file(f"{p}_pl.grib"), f.path)
        tmp.append(f)
    return tmp


def unique_grib_dir():
    def _build_dir_with_grib_files(testdir):
        os.makedirs(testdir, exist_ok=True)
        for p in ["t", "u", "v"]:
            shutil.copy(earthkit_test_data_file(f"{p}_pl.grib"), testdir)

    tmp = temp_directory()
    _build_dir_with_grib_files(tmp.path)
    return tmp


# def list_of_dicts():
#     prototype = {
#         "gridType": "regular_ll",
#         "Nx": 2,
#         "Ny": 3,
#         "distinctLatitudes": [-10.0, 0.0, 10.0],
#         "distinctLongitudes": [0.0, 10.0],
#         "_param_id": 167,
#         "values": [[1, 2], [3, 4], [5, 6]],
#         "date": "20180801",
#         "time": "1200",
#     }
#     return [
#         {"param": "t", "levelist": 500, **prototype},
#         {"param": "t", "levelist": 850, **prototype},
#         {"param": "u", "levelist": 500, **prototype},
#         {"param": "u", "levelist": 850, **prototype},
#         {"param": "d", "levelist": 850, **prototype},
#         {"param": "d", "levelist": 600, **prototype},
#     ]


def install_handle_counter(monkeypatch):
    """Count the eccodes handles created from files or messages.

    Returns a dict whose ``"n"`` item is the number of handles created so far.
    """
    import eccodes

    counter = {"n": 0}

    def _wrap(name):
        orig = getattr(eccodes, name)

        def _new(*args, **kwargs):
            counter["n"] += 1
            return orig(*args, **kwargs)

        monkeypatch.setattr(eccodes, name, _new)

    _wrap("codes_new_from_file")
    _wrap("codes_new_from_message")
    return counter


def install_scan_counter(monkeypatch):
    """Record the base names of the GRIB files scanned by the index."""
    from earthkit.data.readers.grib.index import GribIndex

    scanned = []
    orig = GribIndex._scan

    def _scan(self, path, extra_keys):
        scanned.append(os.path.basename(path))
        return orig(self, path, extra_keys)

    monkeypatch.setattr(GribIndex, "_scan", _scan)
    return scanned


def get_tmp_fixture(input_mode):
    tmp = {
        "directory": unique_grib_dir,
        "file": unique_grib_file,
        "multi": unique_grib_file_list,
    }[input_mode]()

    if isinstance(tmp, list):
        return tmp, [x.path for x in tmp]
    else:
        return tmp, tmp.path
