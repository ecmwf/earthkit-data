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

here = os.path.dirname(__file__)
sys.path.insert(0, here)

from conftest import build_lod_fieldlist  # noqa: E402


@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_metadata(lod_ll_flat, mode):
    build_lod_fieldlist(lod_ll_flat, mode)
