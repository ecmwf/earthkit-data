# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


try:
    # NOTE: the `version.py` file must not be present in the git repository
    #   as it is generated by setuptools at install time
    from ._version import __version__
except ImportError:  # pragma: no cover
    # Local copy or not installed with setuptools
    __version__ = "999"

from earthkit.data.translators import transform
from earthkit.data.wrappers import get_wrapper as from_object

from .arguments.transformers import ALL
from .core.caching import CACHE as cache
from .core.fieldlist import Field
from .core.fieldlist import FieldList
from .core.settings import SETTINGS as settings
from .indexing.fieldlist import SimpleFieldList
from .readers.grib.output import new_grib_output
from .sources import Source
from .sources import from_source
from .sources import from_source_lazily
from .sources.array_list import ArrayField
from .utils.examples import download_example_file
from .utils.examples import remote_example_file

__all__ = [
    "ALL",
    "ArrayField",
    "cache",
    "download_example_file",
    "Field",
    "FieldList",
    "from_source",
    "from_source_lazily",
    "from_object",
    "transform",
    "new_grib_output",
    "remote_example_file",
    "settings",
    "SimpleFieldList",
    "Source",
    "__version__",
]
