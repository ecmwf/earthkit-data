#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import mimetypes

import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_file


def test_geojson():
    for s in from_source("file", earthkit_file("tests/data/NUTS_RG_20M_2021_3035.geojson")):
        s is not None


# def test_csv_mimetypes():
    # assert mimetypes.guess_type("x.geojson") == ("application/geo+json", None)
    # assert mimetypes.guess_type("x.geojson.gz") == ("application/geo+json", "gzip")
    # assert mimetypes.guess_type("x.geojson.bz2") == ("application/geo+json", "bzip2")


# TODO test compression

if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
