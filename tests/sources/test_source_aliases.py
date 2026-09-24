#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import warnings

import pytest

from earthkit.data import sources
from earthkit.data.sources.utils import _preprocess_name


def test_wekeocds_alias_old_name_warns():
    with pytest.warns(FutureWarning, match="wekeocds"):
        assert _preprocess_name("wekeocds") == "wekeo-cds"


def test_wekeocds_alias_new_name_no_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        assert _preprocess_name("wekeo-cds") == "wekeo-cds"


def test_from_source_resolves_deprecated_alias(monkeypatch):
    monkeypatch.setitem(sources.POSSIBLE_SOURCES, "wekeo-cds", lambda *args, **kwargs: (args, kwargs))
    with pytest.warns(FutureWarning, match="use 'wekeo-cds' instead"):
        assert sources.from_source("wekeocds", "ds", x=1) == (("ds",), {"x": 1})


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
