#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import threading

import pytest

import earthkit.data
from earthkit.data import settings


@pytest.mark.skip(reason="to be improved")
def test_thread_url_cache(tmpdir):
    with settings.temporary(cache_policy="off", temporary_directory_root=str(tmpdir)):

        def worker(n):
            # print(f"Thread {n}: loading data", flush=True)
            ds = earthkit.data.from_source("sample", "test.grib")
            # print(f"Thread {n}: got {len(ds)} messages", flush=True)
            assert len(ds) == 2

        settings.set("cache-policy", "off")

        threads = []
        nums = list(range(10))

        for n in nums:
            thread = threading.Thread(target=worker, args=(n,))
            # print("Starting thread", n, flush=True)
            thread.start()
            threads.append(thread)

        for n, thread in zip(nums, threads):
            # print("Joining thread", n, flush=True)
            thread.join()
