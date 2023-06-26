#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file


def test_grib_save_when_loaded_from_file():
    fs = from_source("file", earthkit_examples_file("test6.grib"))
    assert len(fs) == 6
    with temp_file() as tmp:
        fs.save(tmp)
        fs_saved = from_source("file", tmp)
        assert len(fs) == len(fs_saved)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
