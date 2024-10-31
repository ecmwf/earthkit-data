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

from earthkit.data.sources.file import FileSourcePathAndParts
from earthkit.data.utils.parts import SimplePart
from earthkit.data.utils.url import UrlSourcePathAndParts


@pytest.mark.parametrize(
    "paths,parts,expected_paths,expected_parts",
    [
        ("a.grib", None, "a.grib", None),
        (["a.grib"], [None], "a.grib", None),
        ("a.grib", [None], "a.grib", None),
        (["a.grib", None], None, "a.grib", None),
        (["a.grib", [(0, 150)]], None, "a.grib", (SimplePart(0, 150),)),
        (["a.grib", (0, 150)], None, "a.grib", (SimplePart(0, 150),)),
        ("a.grib", [(0, 150)], "a.grib", (SimplePart(0, 150),)),
        ("a.grib", [(0, 150), (150, 100)], "a.grib", (SimplePart(0, 250),)),
        (
            "a.grib",
            [(0, 150), (160, 100)],
            "a.grib",
            (SimplePart(0, 150), SimplePart(160, 100)),
        ),
        (
            "a.grib",
            [(150, 100), (0, 150)],
            ("a.grib", "a.grib"),
            ((SimplePart(150, 100),), (SimplePart(0, 150),)),
        ),
        (["a.grib", "b.grib"], None, ["a.grib", "b.grib"], [None, None]),
        (
            ["a.grib", "b.grib"],
            (0, 150),
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150),), (SimplePart(0, 150),)),
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], "b.grib"],
            None,
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150), SimplePart(200, 20)), None),
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", (0, 100)]],
            None,
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150), SimplePart(200, 20)), ((SimplePart(0, 100),))),
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", [(0, 100)]]],
            None,
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150), SimplePart(200, 20)), ((SimplePart(0, 100),))),
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", [(0, 100), (120, 50)]]],
            None,
            ("a.grib", "b.grib"),
            (
                (SimplePart(0, 150), SimplePart(200, 20)),
                ((SimplePart(0, 100), SimplePart(120, 50))),
            ),
        ),
        (
            ["a.grib", "b.grib"],
            (0, 150),
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150),), (SimplePart(0, 150),)),
        ),
    ],
)
def test_file_parts_prepare(paths, parts, expected_paths, expected_parts):
    p = FileSourcePathAndParts.from_paths(paths, parts)
    res_paths, res_parts = p.path, p.parts
    assert res_paths == expected_paths
    assert res_parts == expected_parts


def test_file_parts_update_1():
    p = FileSourcePathAndParts.from_paths("", None)
    assert p.path == ""
    assert p.parts is None

    p.update("a.grib")
    assert p.path == "a.grib"
    assert p.parts is None

    p.update(["a.grib", "b.grib"])
    assert p.path == ["a.grib", "b.grib"]
    assert p.parts == [None, None]


def test_file_parts_update_2():
    p = FileSourcePathAndParts.from_paths("", None)
    assert p.path == ""
    assert p.parts is None

    p.update(["a.grib"])
    assert p.path == ["a.grib"]
    assert p.parts == [None]

    p.update("a.grib")
    assert p.path == "a.grib"
    assert p.parts is None


def test_file_parts_iter_1():
    p = FileSourcePathAndParts.from_paths("a.grib", None)
    assert p.path == "a.grib"
    assert p.parts is None

    for pt, pr in p:
        pt == "a.grib"
        pr is None


def test_file_parts_iter_2():
    p = FileSourcePathAndParts.from_paths(["a.grib", "b.grib"], None)
    assert p.path == ["a.grib", "b.grib"]
    assert p.parts == [None, None]

    ref_path = ["a.grib", "b.grib"]
    ref_parts = [None, None]

    i = 0
    for pt, pr in p:
        pt == ref_path[i]
        pr is ref_parts[i]
        i += 1


def test_file_parts_zipped_1():
    p = FileSourcePathAndParts.from_paths("a.grib", None)
    assert p.path == "a.grib"
    assert p.parts is None
    assert p.zipped() == [("a.grib", None)]


def test_file_parts_zipped_2():
    p = FileSourcePathAndParts.from_paths(["a.grib", "b.grib"], None)
    assert p.path == ["a.grib", "b.grib"]
    assert p.parts == [None, None]
    assert p.zipped() == [("a.grib", None), ("b.grib", None)]


@pytest.mark.parametrize(
    "urls,parts,expected_values",
    [
        ("a.grib", None, [("a.grib", None)]),
        (["a.grib", None], None, [("a.grib", None)]),
        (["a.grib", [(0, 150)]], None, [("a.grib", (SimplePart(0, 150),))]),
        (["a.grib", (0, 150)], None, [("a.grib", (SimplePart(0, 150),))]),
        ("a.grib", [(0, 150)], [("a.grib", (SimplePart(0, 150),))]),
        ("a.grib", [(0, 150), (150, 100)], [("a.grib", (SimplePart(0, 250),))]),
        (
            "a.grib",
            [(0, 150), (160, 100)],
            [("a.grib", (SimplePart(0, 150), SimplePart(160, 100)))],
        ),
        (
            "a.grib",
            [(150, 100), (0, 150)],
            [
                ("a.grib", ((SimplePart(150, 100),))),
                ("a.grib", ((SimplePart(0, 150),))),
            ],
        ),
        (["a.grib", "b.grib"], None, [("a.grib", None), ("b.grib", None)]),
        (
            ["a.grib", "b.grib"],
            (0, 150),
            [("a.grib", (SimplePart(0, 150),)), ("b.grib", (SimplePart(0, 150),))],
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], "b.grib"],
            None,
            [("a.grib", (SimplePart(0, 150), SimplePart(200, 20))), ("b.grib", None)],
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", (0, 100)]],
            None,
            [
                ("a.grib", (SimplePart(0, 150), SimplePart(200, 20))),
                ("b.grib", (SimplePart(0, 100),)),
            ],
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", [(0, 100)]]],
            None,
            [
                ("a.grib", (SimplePart(0, 150), SimplePart(200, 20))),
                ("b.grib", (SimplePart(0, 100),)),
            ],
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", [(0, 100), (120, 50)]]],
            None,
            [
                ("a.grib", (SimplePart(0, 150), SimplePart(200, 20))),
                ("b.grib", (SimplePart(0, 100), SimplePart(120, 50))),
            ],
        ),
        (
            ["a.grib", "b.grib"],
            (0, 150),
            [
                ("a.grib", (SimplePart(0, 150),)),
                ("b.grib", (SimplePart(0, 150),)),
            ],
        ),
    ],
)
def test_url_parts_prepare(urls, parts, expected_values):
    p = UrlSourcePathAndParts.from_paths(urls, parts)
    res = p.zipped()
    assert res == expected_values


@pytest.mark.parametrize(
    "paths,parts,expected_paths,expected_parts,same",
    [
        (["a.grib", "b.grib"], None, ["a.grib", "b.grib"], [None, None], True),
        (["b.grib", "a.grib"], None, ["a.grib", "b.grib"], [None, None], False),
        (
            ["b.grib", "a.grib"],
            (0, 150),
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150),), (SimplePart(0, 150),)),
            False,
        ),
        (
            [["b.grib", [(0, 150), (200, 20)]], "a.grib"],
            None,
            ("a.grib", "b.grib"),
            (None, (SimplePart(0, 150), SimplePart(200, 20))),
            False,
        ),
    ],
)
def test_file_parts_sorted(paths, parts, expected_paths, expected_parts, same):
    p = FileSourcePathAndParts.from_paths(paths, parts)
    p1 = p.sorted()

    if same:
        assert list(p1.path) == list(p.path)
    else:
        assert list(p1.path) != list(p.path)

    res_paths, res_parts = p1.path, p1.parts
    assert list(res_paths) == list(expected_paths)
    assert list(res_parts) == list(expected_parts)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
