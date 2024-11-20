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

from earthkit.data.utils.parts import SimplePart
from earthkit.data.utils.url import UrlSpec


@pytest.mark.parametrize(
    "urls,_kwargs,expected_url,expected_parts,expected_items",
    [
        (
            {"url": "a.grib"},
            {},
            ["a.grib"],
            [None],
            [
                (
                    "a.grib",
                    None,
                    {},
                )
            ],
        ),
        (
            {"url": "a.grib", "parts": None},
            {},
            ["a.grib"],
            [None],
            [
                (
                    "a.grib",
                    None,
                    {},
                )
            ],
        ),
        (
            {"url": "a.grib", "parts": (0, 2)},
            {"chunk_size": 12},
            ("a.grib",),
            ((SimplePart(offset=0, length=2),),),
            [
                (
                    "a.grib",
                    (SimplePart(offset=0, length=2),),
                    {"chunk_size": 12},
                )
            ],
        ),
        (
            {
                "url": "a.grib",
                "chunk_size": 12,
            },
            {"parts": (0, 2)},
            ("a.grib",),
            ((SimplePart(offset=0, length=2),),),
            [
                (
                    "a.grib",
                    (SimplePart(offset=0, length=2),),
                    {"chunk_size": 12},
                )
            ],
        ),
        (
            {"url": "a.grib", "parts": [(0, 2), (5, 3)]},
            {"chunk_size": 12},
            ("a.grib",),
            ((SimplePart(offset=0, length=2), SimplePart(offset=5, length=3)),),
            [
                (
                    "a.grib",
                    (SimplePart(offset=0, length=2), SimplePart(offset=5, length=3)),
                    {"chunk_size": 12},
                )
            ],
        ),
        (
            [{"url": "a.grib", "parts": (0, 2)}, {"url": "b.grib"}],
            {"chunk_size": 12},
            ("a.grib", "b.grib"),
            ((SimplePart(offset=0, length=2),), None),
            [
                (
                    "a.grib",
                    (SimplePart(offset=0, length=2),),
                    {"chunk_size": 12},
                ),
                (
                    "b.grib",
                    None,
                    {"chunk_size": 12},
                ),
            ],
        ),
        (
            [{"url": "a.grib", "chunk_size": 12}, {"url": "b.grib"}],
            {"parts": (0, 2)},
            ("a.grib", "b.grib"),
            ((SimplePart(offset=0, length=2),), (SimplePart(offset=0, length=2),)),
            [
                (
                    "a.grib",
                    (SimplePart(offset=0, length=2),),
                    {"chunk_size": 12},
                ),
                (
                    "b.grib",
                    (SimplePart(offset=0, length=2),),
                    {},
                ),
            ],
        ),
        (
            [
                {"url": "a.grib", "chunk_size": 12},
                {"url": "b.grib"},
                "c.grib",
            ],
            {"parts": (0, 2)},
            ("a.grib", "b.grib", "c.grib"),
            (
                (SimplePart(offset=0, length=2),),
                (SimplePart(offset=0, length=2),),
                (SimplePart(offset=0, length=2),),
            ),
            [
                (
                    "a.grib",
                    (SimplePart(offset=0, length=2),),
                    {"chunk_size": 12},
                ),
                (
                    "b.grib",
                    (SimplePart(offset=0, length=2),),
                    {},
                ),
                (
                    "c.grib",
                    (SimplePart(offset=0, length=2),),
                    {},
                ),
            ],
        ),
        (
            [
                {"url": "a.grib", "chunk_size": 12, "parts": (0, 2)},
                {"url": "b.grib"},
                "c.grib",
                ["d.grib", ((0, 5), (9, 3))],
            ],
            {"timeout": 12},
            ("a.grib", "b.grib", "c.grib", "d.grib"),
            (
                (SimplePart(offset=0, length=2),),
                None,
                None,
                (SimplePart(offset=0, length=5), SimplePart(offset=9, length=3)),
            ),
            [
                (
                    "a.grib",
                    (SimplePart(offset=0, length=2),),
                    {"chunk_size": 12, "timeout": 12},
                ),
                (
                    "b.grib",
                    None,
                    {"timeout": 12},
                ),
                (
                    "c.grib",
                    None,
                    {"timeout": 12},
                ),
                (
                    "d.grib",
                    (SimplePart(offset=0, length=5), SimplePart(offset=9, length=3)),
                    {"timeout": 12},
                ),
            ],
        ),
    ],
)
def test_url_spec(urls, _kwargs, expected_url, expected_parts, expected_items):
    r = UrlSpec.from_urls(urls, **_kwargs)

    assert r.url == expected_url
    assert r.parts == expected_parts

    for i, x in enumerate(r):
        assert x == expected_items[i]


@pytest.mark.parametrize(
    "urls,_kwargs,expected_url,expected_parts,expected_items",
    [
        (
            {"url": "a.grib", "parts": (0, 2)},
            {"chunk_size": 1, "parts": (3, 5)},
            ("a.grib",),
            ((SimplePart(offset=0, length=2),),),
            [
                (
                    "a.grib",
                    (SimplePart(offset=0, length=2),),
                    {"chunk_size": 12},
                )
            ],
        ),
    ],
)
def test_url_spec_bad(urls, _kwargs, expected_url, expected_parts, expected_items):
    with pytest.raises(ValueError):
        UrlSpec.from_urls(urls, **_kwargs)


@pytest.mark.parametrize(
    "urls,_kwargs,expected_url,expected_parts,expected_items",
    [
        (
            [{"url": "b.grib", "chunk_size": 12}, {"url": "a.grib"}],
            {"parts": (0, 2)},
            ("a.grib", "b.grib"),
            ((SimplePart(offset=0, length=2),), (SimplePart(offset=0, length=2),)),
            [
                (
                    "a.grib",
                    (SimplePart(offset=0, length=2),),
                    {},
                ),
                (
                    "b.grib",
                    (SimplePart(offset=0, length=2),),
                    {"chunk_size": 12},
                ),
            ],
        ),
    ],
)
def test_url_spec_sorted(urls, _kwargs, expected_url, expected_parts, expected_items):
    r = UrlSpec.from_urls(urls, **_kwargs)
    r1 = r.sorted()

    assert r1.url != r.url
    # assert r1.parts != r.parts
    assert r1.url == expected_url
    assert r1.parts == expected_parts

    for i, x in enumerate(r1):
        assert x == expected_items[i]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
