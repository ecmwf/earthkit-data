# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import SimpleTarget

LOG = logging.getLogger(__name__)


class GribIndexTarget(SimpleTarget):
    """
    File target.

    Parameters
    ----------
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

    Raises
    ------
    ValueError: If the file name is not specified and cannot be constructed.
    """

    _name = "file"

    def __init__(self, file=None, *, append=False, **kwargs):
        super().__init__(**kwargs)

        self.filename = None
        if isinstance(file, str):
            self.filename = file

    def close(self):
        """Close the file if :obj:`FileTarget` was created with a file path.

        If :obj:`FileTarget` was created with a file object this call has no effect.
        The target will not be able to write anymore.

        Raises
        ------
        ValueError: If the target is already closed.
        """
        pass

    def flush(self):
        """Flush the file.

        Raises
        ------
        ValueError: If the target is already closed.
        """
        pass

    def _write(self, data=None, **kwargs):
        # from earthkit.data.readers.grib.index import GribIndex

        self._encode(data, suffix=self.ext, db_path=self.filename, **kwargs)

        # data_path = None
        # if isinstance(data, str):
        #     data_path = data
        # elif hasattr(data, "path"):
        #     data_path = data.path

        # if data_path:
        #     grib_index = GribIndex.from_file(data_path, db_path=self.filename, **kwargs)
        # else:
        #     grib_index = GribIndex.from_fieldlist(data, db_path=self.filename, **kwargs)

        # if not self._check_overwrite(data):
        #     return

        # r = self._encode(data, suffix=self.ext, **kwargs)
        # if hasattr(r, "__iter__"):
        #     f = self._f()
        #     for d in r:
        #         d.to_file(f)
        # else:
        #     if self.filename and r.prefer_file_path:
        #         r.to_file(self.filename)
        #     else:
        #         r.to_file(self._f())


target = GribIndexTarget
