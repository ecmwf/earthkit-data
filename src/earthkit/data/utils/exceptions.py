# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


class EmptyFileError(Exception):
    """Exception raised when attempting to read or process an empty file.

    This exception is raised when a file is found to be empty (zero bytes)
    and the operation requires the file to contain data.
    """

    pass
