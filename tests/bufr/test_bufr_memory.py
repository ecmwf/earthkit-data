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
from earthkit.data.utils.testing import earthkit_examples_file


def test_bufr_from_memory_single():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")).to_featurelist()
    data = ds[0].message()

    fs = from_source("memory", data).to_featurelist()
    assert len(fs) == 1
    assert fs.metadata("dataCategory") == [2]
    assert fs[0].metadata("ident") == "02836"


def test_bufr_from_memory_multi():
    with open(earthkit_examples_file("temp_10.bufr"), "rb") as f:
        data = f.read()
        fs = from_source("memory", data).to_featurelist()
        assert len(fs) == 10
        assert fs.metadata("dataCategory") == [2] * 10
        assert fs[0].metadata("ident") == "02836"
        assert fs[-1].metadata("ident") == "02963"


def test_bufr_save_when_loaded_from_memory():
    with open(earthkit_examples_file("temp_10.bufr"), "rb") as f:
        data = f.read()
        fs = from_source("memory", data).to_featurelist()
        with temp_file() as tmp:
            fs.to_target("file", tmp)
            fs_saved = from_source("file", tmp).to_featurelist()
            assert len(fs) == len(fs_saved)
            assert fs_saved.metadata("dataCategory") == [2] * 10


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main()
