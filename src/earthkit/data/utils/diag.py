# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import time
from collections import defaultdict


class DiagCore:
    def __init__(self, name=""):
        self.name = name

    def _build_label(self, label):
        if label:
            label = f"[{label:10}] "

        if self.name:
            name = f"[{self.name:10}] "
            if label:
                label = f"{name}{label}"
            else:
                label = f"{name}"

        return label


class TimeDiag(DiagCore):
    def __init__(self, name="", **kwargs):
        self.start = time.time()
        self.prev = self.start
        super().__init__(name=name, **kwargs)

    def elapsed(self):
        return time.time() - self.start

    def __call__(self, label="", as_str=False):
        curr = time.time()
        delta = curr - self.prev
        self.prev = curr
        label = self._build_label(label)
        s = f"{label}elapsed={self.elapsed():.3f}s delta={delta:.3f}s"

        if as_str:
            return s
        else:
            print(s)


class MemoryDiag(DiagCore):
    def __init__(self, name="", peak=False, **kwargs):
        import os
        import platform

        import psutil

        self.proc = psutil.Process()
        self.prev = 0
        self.scale = 1
        self.add_peak = peak

        try:
            if os.name == "posix" and platform.system() == "Darwin":
                self.scale = 1.0 / (1024 * 1024)
        except Exception:
            pass

        super().__init__(name=name, **kwargs)

    def scale_to_mbytes(self, v):
        return v * self.scale

    def current(self):
        """Current rss memory usage in MB."""
        import gc

        gc.collect()
        attrs = ["memory_info"]
        mem = self.proc.as_dict(attrs=attrs).get("memory_info", None)
        if mem is not None:
            return self.scale_to_mbytes(mem._asdict()["rss"])
        return 0

    def peak(self):
        """Peak rss memory usage in MB."""
        from resource import RUSAGE_SELF
        from resource import getrusage

        rss = getrusage(RUSAGE_SELF).ru_maxrss
        return self.scale_to_mbytes(rss)

    def __call__(self, label="", delta=True, as_str=False):
        m = self.current()
        _delta = m - self.prev
        self.prev = m
        label = self._build_label(label)

        s = ""
        if delta:
            s = f"{label}curr={m:.3f}MB delta={_delta:.3f}MB"
        else:
            s = f"{label}curr={m:.3f}MB"

        if self.add_peak:
            s += f" peak={self.peak():.3f}MB"

        if as_str:
            return s
        else:
            print(s)


class Diag(DiagCore):
    def __init__(self, name="", peak=False, **kwargs):
        self.time = TimeDiag("")
        self.memory = MemoryDiag("", peak=peak)
        super().__init__(name=name, **kwargs)

    def __call__(self, label=""):
        label = str(label)
        label = self._build_label(label)
        s = f"{label}{self.time(as_str=True)} {self.memory(as_str=True)}"
        print(s)

    def peak(self):
        return self.memory.peak()


def metadata_cache_diag(fieldlist):
    r = defaultdict(int)
    for f in fieldlist:
        collect_field_metadata_cache_diag(f, r)
    return r


def collect_field_metadata_cache_diag(field, r):
    try:
        md_cache = field_cache_diag(field)
        for k in ["metadata_cache_hits", "metadata_cache_misses", "metadata_cache_size"]:
            r[k] += md_cache[k]
    except Exception:
        pass


def field_cache_diag(field):
    r = defaultdict(int)
    try:
        md_cache = field.metadata()._cache
        r["metadata_cache_size"] += len(md_cache)
        r["metadata_cache_hits"] += md_cache.hits
        r["metadata_cache_misses"] += md_cache.misses
    except Exception:
        pass
    return r
