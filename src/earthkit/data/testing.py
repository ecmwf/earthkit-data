# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import pathlib
import shutil
from contextlib import contextmanager
from importlib import import_module
from unittest.mock import patch

import numpy as np
from earthkit.utils.array import array_namespace as eku_array_namespace
from earthkit.utils.array import convert as convert_array

# from earthkit.utils.testing import get_array_backend
from earthkit.utils.array.testing import NAMESPACE_DEVICES

from earthkit.data import from_object
from earthkit.data import from_source
from earthkit.data.readers.text import TextReader
from earthkit.data.sources.empty import EmptySource
from earthkit.data.sources.mars import StandaloneMarsClient

LOG = logging.getLogger(__name__)


class OfflineError(Exception):
    pass


_NETWORK_PATCHER = patch("socket.socket", side_effect=OfflineError)

_REMOTE_ROOT_URL = "https://sites.ecmwf.int/repository/earthkit-data/"
_REMOTE_TEST_DATA_URL = "https://sites.ecmwf.int/repository/earthkit-data/test-data/"
_REMOTE_EXAMPLES_URL = "https://sites.ecmwf.int/repository/earthkit-data/examples/"

_ROOT_DIR = top = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if not os.path.exists(os.path.join(_ROOT_DIR, "tests", "data")):
    _ROOT_DIR = "./"


@contextmanager
def network_off():
    try:
        _NETWORK_PATCHER.start()
        yield None
    finally:
        _NETWORK_PATCHER.stop()


@contextmanager
def preserve_cwd():
    current_dir = os.getcwd()
    try:
        yield None
    finally:
        os.chdir(current_dir)


def earthkit_remote_file(*args):
    return os.path.join(_REMOTE_ROOT_URL, *args)


def earthkit_remote_test_data_file(*args):
    return os.path.join(_REMOTE_TEST_DATA_URL, *args)


def earthkit_remote_examples_file(*args):
    return os.path.join(_REMOTE_EXAMPLES_URL, *args)


def earthkit_file(*args):
    return os.path.join(_ROOT_DIR, *args)


def earthkit_examples_file(*args):
    return os.path.join(_ROOT_DIR, "docs", "examples", *args)


def earthkit_test_data_file(*args):
    return os.path.join(_ROOT_DIR, "tests", "data", *args)


def data_file(*args):
    return os.path.join(os.path.dirname(__file__), "data", *args)


def file_url(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()


def data_file_url(*args):
    return file_url(data_file(*args))


def modules_installed(*modules):
    for module in modules:
        try:
            import_module(module)
        except (ImportError, RuntimeError, SyntaxError):
            return False
    return True


NO_MARS_DIRECT = not StandaloneMarsClient.enabled()
NO_MARS_API = not os.path.exists(os.path.expanduser("~/.ecmwfapirc"))
NO_MARS = NO_MARS_API and NO_MARS_DIRECT

NO_CDS = not os.path.exists(os.path.expanduser("~/.cdsapirc"))
NO_HDA = not os.path.exists(os.path.expanduser("~/.hdarc"))
IN_GITHUB = os.environ.get("GITHUB_WORKFLOW") is not None
try:
    import ecmwf.opendata  # noqa

    NO_EOD = False
except Exception:
    NO_EOD = True

try:
    import pyfdb  # noqa

    NO_FDB = False
except Exception:
    NO_FDB = True

NO_PROD_FDB = NO_FDB
if not NO_PROD_FDB:
    fdb_home = os.environ.get("FDB_HOME", None)
    NO_PROD_FDB = fdb_home is None

NO_GRIBJUMP = NO_FDB or not modules_installed("pygribjump")
NO_POLYTOPE = not os.path.exists(os.path.expanduser("~/.polytopeapirc"))
NO_COVJSONKIT = not modules_installed("covjsonkit")
NO_RIOXARRAY = not modules_installed("rioxarray")

NO_S3_AUTH = not modules_installed("aws_requests_auth")
NO_GEO = not modules_installed("earthkit-data")
try:
    NO_ECFS = not os.path.exists(shutil.which("ecp"))
except Exception:
    NO_ECFS = True


NO_ZARR = True
try:
    import zarr  # noqa

    if int(zarr.__version__.split(".")[0]) >= 3:
        NO_ZARR = False
except Exception:
    pass

NO_IRIS = not (modules_installed("iris") and modules_installed("ncdata"))


def MISSING(*modules):
    return not modules_installed(*modules)


UNSAFE_SAMPLES_URL = "https://github.com/jwilk/traversal-archives/releases/download/0"


def empty(ds):
    LOG.debug("%s", ds)
    assert isinstance(ds, EmptySource)
    assert len(ds) == 0


def text(ds):
    LOG.debug("%s", ds)
    assert isinstance(ds._reader, TextReader)


UNSAFE_SAMPLES = (
    ("absolute1", empty),
    ("absolute2", empty),
    ("relative0", empty),
    ("relative2", empty),
    ("symlink", text),
    ("dirsymlink", text),
    ("dirsymlink2a", text),
    ("dirsymlink2b", text),
)


def check_unsafe_archives(extension):
    for archive, check in UNSAFE_SAMPLES:
        LOG.debug("%s.%s", archive, extension)
        ds = from_source("url", f"{UNSAFE_SAMPLES_URL}/{archive}{extension}")
        check(ds)


def load_nc_or_xr_source(path, mode):
    if mode == "nc":
        return from_source("file", path)
    else:
        import xarray

        return from_object(xarray.open_dataset(path))


class ArrayBackend:
    def __init__(self, array_namespace, device=None, dtype=None):
        self._d = (eku_array_namespace(array_namespace), device, dtype)

    @property
    def array_namespace(self):
        return self._d[0]

    @property
    def device(self):
        return self._d[1]

    @property
    def dtype(self):
        return self._d[2]

    def __len__(self):
        return len(self._d)

    def __getitem__(self, index):
        return self._d[index]

    @property
    def name(self):
        return self.array_namespace._earthkit_array_namespace_name


# Array backends
ARRAY_BACKENDS = []
for x in NAMESPACE_DEVICES:
    name = x[0]._earthkit_array_namespace_name
    device = x[1]
    dtype = None
    # if name in ["numpy", "torch", "cupy", "jax"]:
    if name in ["numpy"]:
        if name == "torch" and device.type == "mps":
            dtype = "float32"
        ARRAY_BACKENDS.append(ArrayBackend(x[0], device, dtype))


def make_tgz(target_dir, target_name, paths):
    import tarfile

    with tarfile.open(os.path.join(target_dir, target_name), "w:gz") as tar:
        for p in paths:
            tar.add(p)
    # tar.close()


def make_zip(target_dir, target_name, paths):
    import zipfile

    with zipfile.ZipFile(os.path.join(target_dir, target_name), "a") as zipf:
        for p in paths:
            zipf.write(p)


# Kep for legacy tests
WRITE_TO_FILE_METHODS = []


def write_to_file(mode, path, ds, **kwargs):
    pass


def check_array(
    v,
    shape=None,
    first=None,
    last=None,
    meanv=None,
    eps=1e-3,
):
    v = convert_array(v, array_namespace="numpy")

    assert v.shape == shape, f"{v.shape} != {shape}"
    assert np.isclose(v[0], first, rtol=eps)
    assert np.isclose(v[-1], last, rtol=eps)
    assert np.isclose(v.mean(), meanv, rtol=eps)


def enforce_dtype(array_namespace, device):
    array_namespace = eku_array_namespace(array_namespace)
    if (
        array_namespace._earthkit_array_namespace_name == "torch"
        and isinstance(device, str)
        and device.startswith("mps")
    ):
        return "float32"
    return None


def match_dtype(array, xp, dtype):
    dtype = xp.__array_namespace_info__().dtypes().get(dtype, dtype)
    if dtype is not None:
        return xp.dtype(array) == dtype
    return False


def check_array_type(array, expected_namespace, dtype=None):
    xp1 = eku_array_namespace(array)
    xp2 = eku_array_namespace(expected_namespace)

    if xp2 is None:
        raise ValueError(f"Invalid expected_namespace={expected_namespace}")

    assert xp1 == xp2, f"{xp1=}, {xp2=}"

    expected_dtype = dtype
    if expected_dtype is not None:
        assert match_dtype(array, xp2, expected_dtype), f"{array.dtype}, {expected_dtype=}"
        # assert b2.match_dtype(array, expected_dtype), f"{array.dtype}, {expected_dtype=}"


# # TODO: only tested for numpy an torch (cpu, torch(cpu, mps))
# def to_numpy_dtype(dtype, xp=None):
#     if dtype is None:
#         return np.float64
#     elif isinstance(dtype, str):
#         return np.dtype(dtype)
#     elif xp is not None:
#         for d in xp.__array_namespace_info__().dtypes.items():
#             if d[1] == dtype:
#                 return np.dtype(d[0])

#     if hasattr(dtype, "type"):
#         dtype = dtype.type

#     return dtype


def main(path):
    import sys

    import pytest

    # Parallel does not work on darwin, gets RuntimeError: context has already been set
    # because pytest-parallel changes the context from `spawn` to `fork`

    args = ["-p", "no:parallel", "-E", "release"]

    if len(sys.argv) > 1 and sys.argv[1] == "--no-debug":
        args += ["-o", "log_cli=False"]
    else:
        logging.basicConfig(level=logging.DEBUG)
        args += ["-o", "log_cli=True"]

    args += [path]

    sys.exit(pytest.main(args))
