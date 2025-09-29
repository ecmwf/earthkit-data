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
import time

from earthkit.data.decorators import thread_safe_cached_property


class _A:
    count_static = 0

    def __init__(self, count=0):
        self.count = count

    @thread_safe_cached_property
    def data(self):
        """Property data"""
        time.sleep(1)
        self.count += 1
        return self.count

    @thread_safe_cached_property
    def data_static(self):
        """Property data_static"""
        time.sleep(1)
        self.count_static += 1
        return self.count_static


def test_thread_cached_property_1(reraise):
    a = _A()

    def worker(n):
        with reraise:
            assert a.data == 1, f"Thread {n} failed"

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

    assert a.data == 1
    assert a.count == 1
    assert a.data == 1


def test_thread_cached_property_2(reraise):
    a = _A(0)
    b = _A(1)

    def worker(n):
        with reraise:
            assert a.data == 1, f"a, thread {n} failed"
            assert b.data == 2, f"b, thread {n} failed"

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

    assert a.data == 1
    assert b.data == 2
    assert a.count == 1
    assert b.count == 2
    assert a.data == 1
    assert b.data == 2


def test_thread_cached_property_3(reraise):
    a = _A()

    def worker(n):
        with reraise:
            assert a.data_static == 1, f"Thread {n} failed"

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

    assert a.data_static == 1
    assert a.count_static == 1
    assert a.data_static == 1


def test_thread_cached_property_4(reraise):
    a = _A(0)
    b = _A(1)

    def worker(n):
        with reraise:
            assert a.data_static == 1, f"a, thread {n} failed"
            assert b.data_static == 1, f"b, thread {n} failed"

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

    assert a.data_static == 1
    assert b.data_static == 1
    assert a.count_static == 1
    assert b.count_static == 1
    assert a.data_static == 1
    assert b.data_static == 1


def test_thread_cached_property_docstring():
    _A.data.__doc__ == "Property data"
    _A.data_static.__doc__ == "Property data_static"
