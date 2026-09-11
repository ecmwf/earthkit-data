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
import sys

import pytest

from earthkit.data.sources import _from_source_instance
from earthkit.data.sources.multi_url import MultiUrl
from earthkit.data.utils.testing import (
    earthkit_examples_file,
    earthkit_remote_examples_file,
)


@pytest.mark.skipif(  # TODO: fix
    sys.platform == "win32",
    reason="file:// not working on Windows yet",
)
def test_multi_url_source_parts_file_scheme():
    filename = os.path.abspath(earthkit_examples_file("test.grib"))
    src = MultiUrl(
        f"file://{filename}",
        parts=[
            (0, 4),
            (312, 4),
            (360, 4),
            (672, 4),
        ],
    )
    d = _from_source_instance(src)

    assert d._TYPE_NAME == "GRIB"

    path = d.path
    assert os.path.getsize(path) == 16

    with open(path, "rb") as f:
        assert f.read() == b"GRIB7777GRIB7777"


def test_multi_url_source_grib_netcdf_mixed():
    src = MultiUrl(
        [
            earthkit_remote_examples_file("test.nc"),
            earthkit_remote_examples_file("test.grib"),
        ],
    )
    d = _from_source_instance(src)

    assert d._TYPE_NAME == "Multi"
    assert len(d.path) == 2
    items = [x for x in d]
    assert len(items) == 2
    assert items[0]._TYPE_NAME == "NetCDF"
    assert items[1]._TYPE_NAME == "GRIB"
