# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import warnings
from struct import unpack

import numpy as np

from . import Reader

# CSF value scales
# version 2 datatypes
VS_BOOLEAN = 0xE0  # boolean, always UINT1, values: 0,1 or MV_UINT1
VS_NOMINAL = 0xE2  # nominal, UINT1 or INT4
VS_ORDINAL = 0xF2  # ordinal, UINT1 or INT4
VS_SCALAR = 0xEB  # scalar, REAL4 or (maybe) REAL8
VS_DIRECTION = 0xFB  # directional REAL4 or (maybe) REAL8, -1 means no direction
VS_LDD = 0xF0  # local drain direction, always UINT1, values: 1-9 or MV_UINT1
# this one CANNOT be returned by NOR passed to a csf2 function
VS_UNDEFINED = 100  # just some value different from the rest

# CSF cell representations
# preferred version 2 cell representations
CR_UINT1 = 0x00  # boolean, ldd and small nominal and small ordinal
CR_INT4 = 0x26  # large nominal and large ordinal
CR_REAL4 = 0x5A  # single scalar and single directional
# other version 2 cell representations
CR_REAL8 = 0xDB  # double scalar or directional, no loss of precision


def _replace_missing_u1(cur, new):
    out = np.copy(cur)
    out[cur == 255] = new
    return out


def _replace_missing_i4(cur, new):
    out = np.copy(cur)
    out[cur == -2147483648] = new
    return out


def _replace_missing_f4(cur, new):
    out = np.copy(cur)
    out[np.isnan(cur)] = new
    return out


def _replace_missing_f8(cur, new):
    out = np.copy(cur)
    out[np.isnan(cur)] = new
    return out


CELLREPR = {
    CR_UINT1: {
        "dtype": np.dtype("uint8"),
        "fillmv": _replace_missing_u1,
    },
    CR_INT4: {
        "dtype": np.dtype("int32"),
        "fillmv": _replace_missing_i4,
    },
    CR_REAL4: {
        "dtype": np.dtype("float32"),
        "fillmv": _replace_missing_f4,
    },
    CR_REAL8: {
        "dtype": np.dtype("float64"),
        "fillmv": _replace_missing_f8,
    },
}


def _from_file(path, missin_to_nan):
    """Load a .map file into a numpy array."""
    with open(path, "rb") as f:
        bytes = f.read()

    nbytes_header = 64 + 2 + 2 + 8 + 8 + 8 + 8 + 4 + 4 + 8 + 8 + 8
    _, cellRepr, _, _, _, _, nrRows, nrCols, _, _, _ = unpack("=hhddddIIddd", bytes[64:nbytes_header])

    try:
        celltype = CELLREPR[cellRepr]
    except KeyError:
        raise ValueError(f"{path}: invalid cellRepr value ({cellRepr}) in header")

    dtype = celltype["dtype"]

    size = dtype.itemsize * nrRows * nrCols
    data = np.frombuffer(bytes[256 : 256 + size], dtype)
    if missin_to_nan:
        data = celltype["fillmv"](data.astype(np.float64), np.nan)

    return data.reshape((nrRows, nrCols))


class PCRasterReader(Reader):
    def __init__(self, source, path, **kwargs):
        if kwargs:
            names = ", ".join(repr(name) for name in kwargs)
            warnings.warn(
                f"Arguments {names} have no effect for the PCRaster reader.",
                UserWarning,
                stacklevel=2,
            )
        super().__init__(source, path)

    def to_numpy(self, missing_to_nan=True):
        return _from_file(self.path, missing_to_nan=missing_to_nan)

    def to_data_object(self, **kwargs):
        from earthkit.data.data.pcraster import PCRasterData

        return PCRasterData(self)

    def _encode_default(self, encoder, *args, **kwargs):
        return None


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if magic is not None:
        if path[-4:] == ".map":
            return PCRasterReader(source, path, **kwargs)


READER = reader
