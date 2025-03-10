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
import re

from . import SimpleTarget

LOG = logging.getLogger(__name__)


class FilePatternTarget(SimpleTarget):
    """
    File target with a pattern for the output file names.

    Parameters:
    -----------
    path: str
        The file path to write to. The output file name defines a pattern containing metadata keys in the
        format of ``{key}``. Each data item (e.g. a field) will be written into a file
        with a name created by substituting the relevant metadata values in the
        filename pattern.
    append: bool
        If True, the files are opened in append mode. Only used if file is a path.
    **kwargs:
        Additional keyword arguments passed to the parent class
    """

    def __init__(self, path, *, append=False, **kwargs):
        super().__init__(**kwargs)

        self._files = {}
        self.filename = path
        self.append = append
        self.ext = None

        if not self.filename:
            raise ValueError("Please provide an output filename")

        _, self.ext = os.path.splitext(self.filename)

        self.split_output = re.findall(r"\{(.*?)\}", self.filename)

        # change format pattern to use positional arguments. This allows using keys
        # containing a dot, e.g. mars.param
        for i, s in enumerate(self.split_output):
            if ":" in s:
                pos_key = f"{i}:" + s.split(":")[1]
            else:
                pos_key = f"{i}"

            self.filename = self.filename.replace(f"{s}", pos_key)

    def close(self):
        """Close the target and closing all the files.

        The target will not be able to write anymore.

        Raises:
        -------
        ValueError: If the target is already closed.
        """
        self._mark_closed()
        for f in self._files.values():
            f.close()

    def flush(self):
        """Flush all the files.

        -------
        ValueError: If the target is already closed.
        """
        for f in self._files.values():
            f.flush()

    def _f(self, data):
        self._raise_if_closed()

        keys = [data.metadata(k.split(":")[0]) for k in self.split_output]
        path = self.filename.format(*keys)

        if path not in self._files:
            flag = "wb" if not self.append else "ab"
            self._files[path] = open(path, flag)

        return self._files[path], path

    def _write(self, data, **kwargs):
        r = self._encode(data, suffix=self.ext, **kwargs)
        if hasattr(r, "__iter__"):
            for d in r:
                f, _ = self._f(d)
                d.to_file(f)
        else:
            f, _ = self._f(r)
            r.to_file(f)


target = FilePatternTarget
