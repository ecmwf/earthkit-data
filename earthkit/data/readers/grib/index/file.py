# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import json
import logging
import os

from earthkit.data.core.caching import auxiliary_cache_file
from earthkit.data.readers.grib.codes import get_messages_positions
from earthkit.data.readers.grib.index import FieldListInFiles
from earthkit.data.utils.parts import Part

LOG = logging.getLogger(__name__)


class FieldlistMessagePositionIndex:
    def __init__(self, path):
        self.path = path
        self.offsets = None
        self.lengths = None
        self._cache_file = None
        self._load()

    def _build(self):
        offsets = []
        lengths = []

        for offset, length in get_messages_positions(self.path):
            offsets.append(offset)
            lengths.append(length)

        self.offsets = offsets
        self.lengths = lengths

    def _load(self):
        if True:
            # if SETTINGS.policy("message-position-cache"):
            self._cache_file = auxiliary_cache_file(
                "grib-index",
                self.path,
                content="null",
                extension=".json",
            )
            if not self._load_cache():
                self._build()
                self._save_cache()
        else:
            self._build()

    def _save_cache(self):
        # assert SETTINGS.policy("message-position-cache")
        try:
            with open(self._cache_file, "w") as f:
                json.dump(
                    dict(
                        version=self.VERSION,
                        offsets=self.offsets,
                        lengths=self.lengths,
                    ),
                    f,
                )
        except Exception:
            LOG.exception("Write to cache failed %s", self._cache_file)

    def _load_cache(self):
        # assert SETTINGS.policy("message-position-cache")
        try:
            with open(self._cache_file) as f:
                c = json.load(f)
                if not isinstance(c, dict):
                    return False

                assert c["version"] == self.VERSION
                self.offsets = c["offsets"]
                self.lengths = c["lengths"]
                return True
        except Exception:
            LOG.exception("Load from cache failed %s", self._cache_file)

        return False


class FieldListInOneFile(FieldListInFiles):
    VERSION = 1

    @property
    def availability_path(self):
        return os.path.join(self.path, ".availability.pickle")

    def __init__(self, path, **kwargs):
        assert isinstance(path, str), path

        self.path = path
        self.position_index = FieldlistMessagePositionIndex(self.path)

        super().__init__(**kwargs)

    def part(self, n):
        return Part(
            self.path, self.position_index.offsets[n], self.position_index.lengths[n]
        )

    def number_of_parts(self):
        return len(self.position_index.offsets)
