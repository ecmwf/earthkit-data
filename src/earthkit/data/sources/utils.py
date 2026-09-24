# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from earthkit.data.data import Data  # type: ignore[import]
    from earthkit.data.sources import Source


# Maps alternative source names to the name the source is registered under
_ALIASES = {
    "wekeocds": "wekeo-cds",
}

# Source names that emit a FutureWarning when used
_DEPRECATED = {"wekeocds"}


def _preprocess_name(name):
    """Resolve a source name through :data:`_ALIASES`.

    Parameters
    ----------
    name : str
        The name of the source. Can be an alias.

    Returns
    -------
    str
        The name the source is registered under.

    Warns
    -----
    FutureWarning
        If ``name`` is in :data:`_DEPRECATED`. When it is also an alias, the warning names
        the alias target as the preferred name to use instead.

    """
    if name in _DEPRECATED:
        if name in _ALIASES:
            warnings.warn(
                f"Source name '{name}' is deprecated, use '{_ALIASES[name]}' instead",
                FutureWarning,
            )
        else:
            warnings.warn(f"Source name '{name}' is deprecated", FutureWarning)

    return _ALIASES.get(name, name)


def _mutate_source(src: "Source") -> "Source":
    prev = None
    while src is not prev:
        prev = src
        src = src.mutate()

    return src


def _from_source_instance(src: "Source") -> "Data":
    src = _mutate_source(src)

    if hasattr(src, "to_data_object"):
        data = src.to_data_object()
        if data is not None:
            return data

    raise ValueError(f"Source {src} cannot be converted into a data object")
