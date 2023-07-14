#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data import from_source
from earthkit.data.core.metadata import Metadata, RawMetadata
from earthkit.data.readers.grib.metadata import GribMetadata
from earthkit.data.testing import earthkit_examples_file


def test_abstract_metadata():
    # Metadata properties:
    # * immutable
    # * behaves like a dict
    # * can be updated (creating a new object, either a copy or a view)
    # Updates can be made with compatible subclasses, e.g. update a GribMetadata with a RawMetadata
    assert Metadata is not None


def test_raw_metadata():
    assert RawMetadata is not None
    assert issubclass(RawMetadata, Metadata)

    md = RawMetadata({"shortName": "2t", "perturbationNumber": 5})
    assert md["shortName"] == "2t"
    assert md["perturbationNumber"] == 5
    assert md.get("shortName") == "2t"
    with pytest.raises(KeyError):
        md["nonExistentKey"]
    assert md.get("nonExistentKey", 12) == 12

    md2 = md.update({"centre": "ecmf", "perturbationNumber": 8})
    sentinel = object()
    assert md.get("centre", sentinel) is sentinel
    assert md["perturbationNumber"] == 5
    assert md2["shortName"] == "2t"
    assert md2["perturbationNumber"] == 8
    assert md2["centre"] == "ecmf"

    md3 = RawMetadata({"step": 24, "centre": "unknown"}).update(md2)
    assert md3["step"] == 24
    assert md3["centre"] == "ecmf"
    assert md3["shortName"] == "2t"


def test_grib_metadata():
    assert GribMetadata is not None
    assert issubclass(GribMetadata, Metadata)

    with pytest.raises(TypeError):
        GribMetadata({"shortName": "u", "typeOfLevel": "pl", "levelist": 1000})

    f = from_source("file", earthkit_examples_file("test.grib"))
    md = f[0].metadata()

    assert isinstance(md, GribMetadata)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
