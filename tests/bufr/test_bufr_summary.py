#!/usr/bin/env python3

# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

from emohawk import load_from
from emohawk.testing import emohawk_examples_file


def test_bufr_ls_invalid_num():
    f = load_from("file", emohawk_examples_file("temp_10.bufr"))
    with pytest.raises(ValueError):
        f.ls(n=0, print=False)

    with pytest.raises(ValueError):
        f.ls(0, print=False)


def test_bufr_ls_num():
    f = load_from("file", emohawk_examples_file("temp_10.bufr"))

    # default keys

    # head
    df = f.ls(n=2, print=False)
    ref = {
        "edition": {0: 3, 1: 3},
        "Type": {0: 2, 1: 2},
        "Subtype": {0: 101, 1: 101},
        "C": {0: 98, 1: 98},
        "Mv": {0: 13, 1: 13},
        "Lv": {0: 1, 1: 1},
        "Subsets": {0: 1, 1: 1},
        "Compr": {0: 0, 1: 0},
        "typicalDate": {0: "20081208", 1: "20081208"},
        "typicalTime": {0: "120000", 1: "120000"},
        "ident": {0: "02836", 1: "01400"},
        "lat": {0: 67.37, 1: 56.9},
        "lon": {0: 26.63, 1: 3.35},
    }

    assert ref == df.to_dict()

    # t tail
    df = f.ls(-2, print=False)
    ref = {
        "edition": {0: 3, 1: 3},
        "Type": {0: 2, 1: 2},
        "Subtype": {0: 101, 1: 101},
        "C": {0: 98, 1: 98},
        "Mv": {0: 13, 1: 13},
        "Lv": {0: 1, 1: 1},
        "Subsets": {0: 1, 1: 1},
        "Compr": {0: 0, 1: 0},
        "typicalDate": {0: "20081208", 1: "20081208"},
        "typicalTime": {0: "120000", 1: "120000"},
        "ident": {0: "11035", 1: "02963"},
        "lat": {0: 48.25, 1: 60.82},
        "lon": {0: 16.37, 1: 23.5},
    }

    assert ref == df.to_dict()

    df = f.ls(-2, print=False)
    assert ref == df.to_dict()


def test_bufr_head_num():
    f = load_from("file", emohawk_examples_file("temp_10.bufr"))

    # default keys
    df = f.head(n=2, print=False)
    ref = {
        "edition": {0: 3, 1: 3},
        "Type": {0: 2, 1: 2},
        "Subtype": {0: 101, 1: 101},
        "C": {0: 98, 1: 98},
        "Mv": {0: 13, 1: 13},
        "Lv": {0: 1, 1: 1},
        "Subsets": {0: 1, 1: 1},
        "Compr": {0: 0, 1: 0},
        "typicalDate": {0: "20081208", 1: "20081208"},
        "typicalTime": {0: "120000", 1: "120000"},
        "ident": {0: "02836", 1: "01400"},
        "lat": {0: 67.37, 1: 56.9},
        "lon": {0: 26.63, 1: 3.35},
    }

    assert ref == df.to_dict()

    df = f.head(2, print=False)
    assert ref == df.to_dict()


def test_bufr_tail_num():
    f = load_from("file", emohawk_examples_file("temp_10.bufr"))

    # default keys
    df = f.tail(n=2, print=False)
    ref = {
        "edition": {0: 3, 1: 3},
        "Type": {0: 2, 1: 2},
        "Subtype": {0: 101, 1: 101},
        "C": {0: 98, 1: 98},
        "Mv": {0: 13, 1: 13},
        "Lv": {0: 1, 1: 1},
        "Subsets": {0: 1, 1: 1},
        "Compr": {0: 0, 1: 0},
        "typicalDate": {0: "20081208", 1: "20081208"},
        "typicalTime": {0: "120000", 1: "120000"},
        "ident": {0: "11035", 1: "02963"},
        "lat": {0: 48.25, 1: 60.82},
        "lon": {0: 16.37, 1: 23.5},
    }

    assert ref == df.to_dict()

    df = f.tail(2, print=False)
    assert ref == df.to_dict()
