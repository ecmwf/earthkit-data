# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .. import Reader


# TODO: this data consists of multiple files and requires a special reader to handle this. The current implementation disables all encoding of this data.
class ShapefileReaderBase(Reader):
    _format = None
    _binary = True
    _appendable = False
