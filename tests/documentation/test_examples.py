#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

import pytest

from earthkit.data.testing import earthkit_file

IGNORE = [
    "conf.py",
    "xml2rst.py",
    "actions.py",
    "generate-examples-maps.py",
    "config-set.py",
    "config-reset.py",
    "config-temporary.py",
    "xref.py",
    "skip_api_rules.py",
    "deprec_settings.py",
    "migrated_settings.py",
]

EXAMPLES = earthkit_file("docs")


def example_list():
    examples = []
    for root, _, files in os.walk(EXAMPLES):
        for file in files:
            path = os.path.join(root, file)
            if path.endswith(".py") and file not in IGNORE:
                n = len(EXAMPLES) + 1
                examples.append(path[n:])

    return sorted(examples)


# # @pytest.mark.skipif(not IN_GITHUB, reason="Not on GITHUB")
# @pytest.mark.parametrize("path", example_list())
# def test_example(path):
#     full = os.path.join(EXAMPLES, path)
#     with open(full) as f:
#         exec(f.read(), dict(__file__=full), {})


@pytest.mark.parametrize("path", example_list())
def test_example(tmpdir, path):
    print("test_example path=", path)
    full = os.path.join(EXAMPLES, path)
    if not full.startswith("/"):
        full = os.path.join(os.getcwd(), full)
    print("  ->", full)
    with tmpdir.as_cwd():
        with open(full) as f:
            exec(f.read(), dict(__file__=full), {})


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
