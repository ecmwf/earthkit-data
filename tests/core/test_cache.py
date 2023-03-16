#!/usr/bin/env python3

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

import pytest

from emohawk import from_source, settings
from emohawk.core.caching import cache_entries, cache_file, purge_cache

LOG = logging.getLogger(__name__)


def test_cache_1():

    purge_cache(matcher=lambda e: ["owner"] == "test_cache")

    def touch(target, args):
        assert args["foo"] in (1, 2)
        with open(target, "w"):
            pass

    path1 = cache_file(
        "test_cache",
        touch,
        {"foo": 1},
        extension=".test",
    )

    path2 = cache_file(
        "test_cache",
        touch,
        {"foo": 2},
        extension=".test",
    )

    assert path1 != path2

    cnt = 0
    for f in cache_entries():
        if f["owner"] == "test_cache":
            cnt += 1

    assert cnt == 2


# 1GB ram disk on MacOS (blocks of 512 bytes)
# diskutil erasevolume HFS+ "RAMDisk" `hdiutil attach -nomount ram://2097152`
@pytest.mark.skipif(not os.path.exists("/Volumes/RAMDisk"), reason="No RAM disk")
def test_cache_4():
    with settings.temporary():
        settings.set("cache-directory", "/Volumes/RAMDisk/emohawk")
        settings.set("maximum-cache-disk-usage", "90%")
        for n in range(10):
            from_source("dummy-source", "zeros", size=100 * 1024 * 1024, n=n)


if __name__ == "__main__":
    from emohawk.testing import main

    main(__file__)
