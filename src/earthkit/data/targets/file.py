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
from io import IOBase

from . import SimpleTarget

LOG = logging.getLogger(__name__)


class FileTarget(SimpleTarget):
    """
    File target.

    Parameters:
    -----------
    file: str, file-like, None
        The file path or file-like object to write to. When None, tries to guess the file name
        from the ``data`` if it is passed as a kwarg.
        When the file name cannot be constructed, a ValueError is raised.
        When ``file`` is a path, a file object is automatically created and closed when the target is closed.
        When ``file`` is a file object, its ownership is not transferred to the target. As a consequence,
        the file object is not closed when the target is closed, even if :obj:`close` is called explicitly.
    append: bool
        If True, the file is opened in append mode. Only used if ``file`` is a path.
    **kwargs:
        Additional keyword arguments passed to the parent class.

    Raises:
    -------
    ValueError: If the file name is not specified and cannot be constructed.
    """

    def __init__(self, file=None, *, append=False, **kwargs):
        super().__init__(**kwargs)

        self.fileobj = None
        self._tmp_fileobj = None
        self.filename = None
        self.append = append
        self.ext = None

        if isinstance(file, IOBase):
            self.fileobj = file
        else:
            self.filename = file
            if self.filename is not None:
                _, self.ext = os.path.splitext(self.filename)

            if self.filename is None:
                self.filename = self._guess_filename(*kwargs)

            if not self.filename:
                raise ValueError("Please provide an output filename")

    def close(self):
        """Close the file if :obj:`FileTarget` was created with a file path.

        If :obj:`FileTarget` was created with a file object this call has no effect.
        The target will not be able to write anymore.

        Raises:
        -------
        ValueError: If the target is already closed.
        """
        self._mark_closed()
        if self._tmp_fileobj:
            self._tmp_fileobj.close()

    def flush(self):
        """Flush the file.

        Raises:
        -------
        ValueError: If the target is already closed.
        """
        self._f().flush()

    def _f(self):
        self._raise_if_closed()

        if self.fileobj:
            return self.fileobj

        if not self._tmp_fileobj:
            flag = "wb" if not self.append else "ab"
            self._tmp_fileobj = open(self.filename, flag)
        return self._tmp_fileobj

    def _guess_filename(self, data=None):
        """Try to guess filename from data when not provided"""
        if data is not None:
            for attr in ["source_filename", "path"]:
                if hasattr(self, attr) and getattr(self, attr) is not None:
                    return [os.path.basename(getattr(self, attr))]

    def _check_overwrite(self, data):
        """Ensure we do not overwrite file that is being read"""
        if (
            data is not None
            and self.filename is not None
            and os.path.isfile(self.filename)
            and hasattr(data, "path")
            and data.path is not None
            and os.path.isfile(data.path)
            and os.path.samefile(self.filename, data.path)
        ):
            import warnings

            warnings.warn(UserWarning(f"Earthkit refusing to overwrite the file being read: {self.filename}"))
            return False
        return True

    def _write(self, data=None, **kwargs):
        if not self._check_overwrite(data):
            return

        r = self._encode(data, suffix=self.ext, **kwargs)
        if hasattr(r, "__iter__"):
            f = self._f()
            for d in r:
                d.to_file(f)
        else:
            if self.filename and r.prefer_file_path:
                r.to_file(self.filename)
            else:
                r.to_file(self._f())


target = FileTarget
