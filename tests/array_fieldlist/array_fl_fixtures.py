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

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.indexing.fieldlist import FieldList
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import get_array_backend


def load_array_fl(num, array_backend=None):
    assert num in [1, 2, 3]
    files = ["test.grib", "test6.grib", "tuv_pl.grib"]
    files = files[:num]

    ds_in = []
    md = []
    for fname in files:
        ds = from_source("file", earthkit_examples_file(fname))
        ds_in.append(ds.to_fieldlist(array_backend=array_backend))
        md += ds_in[-1].get("param")

    ds = []
    for x in ds_in:
        # print("len", len(x))
        # ds.append(FieldList.from_array(x.values, [m.override(edition=1) for m in x.metadata()]))
        ds.append(FieldList.from_fields([x.set(values=x.values) for x in x]))

    return (*ds, md)


def load_array_fl_file(fname, array_backend=None):
    ds_in = from_source("file", earthkit_examples_file(fname))
    ds_in = ds_in.to_fieldlist(array_backend=array_backend)
    md = ds_in.get("param")

    # ds = FieldList.from_array(ds_in.values, [m.override(edition=1) for m in ds_in.metadata()])
    ds = FieldList.from_fields([x.set(values=x.values) for x in ds_in])

    return (ds, md)


def check_array_fl(ds, ds_input, md_full, array_backend=None):
    assert len(ds_input) in [1, 2, 3]

    array_backend = get_array_backend(array_backend)

    assert len(ds) == len(md_full)
    assert ds.get("param") == md_full
    assert array_backend.allclose(ds[0].values, ds_input[0][0].values)

    # # values metadata
    # keys = ["min", "max"]
    # for k in keys:
    #     assert np.isclose(ds[0].metadata(k), ds_input[0][0].metadata(k))

    # check slice
    r = ds[1]
    assert r.get("param") == "msl"

    if len(ds_input) > 1:
        r = ds[1:3]
        assert len(r) == 2
        assert r.get("param") == ["msl", "t"]
        assert r[0].get("param") == "msl"
        assert r[1].get("param") == "t"
        assert array_backend.allclose(r[0].values, ds_input[0][1].values)
        assert array_backend.allclose(r[1].values, ds_input[1][0].values)

        # check sel
        r = ds.sel(param="msl")
        assert len(r) == 1
        assert r.get("grib.shortName") == ["msl"]
        assert r[0].get("param") == "msl"
        assert array_backend.allclose(r[0].values, ds_input[0][1].values)

    if len(ds_input) == 3:
        r = ds[1:13:4]
        assert len(r) == 3
        assert r.get("param") == ["msl", "t", "u"]
        assert r[0].get("param") == "msl"
        assert r[1].get("param") == "t"
        assert r[2].get("param") == "u"


def check_array_fl_from_to_fieldlist(ds, ds_input, md_full, array_backend=None, flatten=False, dtype=None):
    assert len(ds_input) in [1, 2, 3]
    assert len(ds) == len(md_full)
    assert ds.metadata("param") == md_full

    array_backend = get_array_backend(array_backend)

    np_kwargs = {"flatten": flatten, "dtype": dtype}

    assert array_backend.allclose(ds[0].to_array(**np_kwargs), ds_input[0][0].to_array(**np_kwargs))

    assert ds.to_array(**np_kwargs).shape == ds_input[0].to_array(**np_kwargs).shape

    # check slice
    r = ds[1]
    assert r.metadata("param") == "msl"

    if len(ds_input) > 1:
        r = ds[1:3]
        assert len(r) == 2
        assert r.get("param") == ["msl", "t"]
        assert r[0].get("param") == "msl"
        assert r[1].get("param") == "t"
        assert array_backend.allclose(r[0].to_array(**np_kwargs), ds_input[0][1].to_array(**np_kwargs))
        assert array_backend.allclose(r[1].to_array(**np_kwargs), ds_input[1][0].to_array(**np_kwargs))

        # check sel
        r = ds.sel(shortName="msl")
        assert len(r) == 1
        assert r.get("grib.shortName") == ["msl"]
        assert r[0].get("param") == "msl"
        assert array_backend.allclose(r[0].to_array(**np_kwargs), ds_input[0][1].to_array(**np_kwargs))

    if len(ds_input) == 3:
        r = ds[1:13:4]
        assert len(r) == 3
        assert r.get("param") == ["msl", "t", "u"]
        assert r[0].get("param") == "msl"
        assert r[1].get("param") == "t"
        assert r[2].get("param") == "u"


def check_save_to_disk(ds, len_ref, meta_ref):
    tmp = temp_file()
    ds.to_target("file", tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == len_ref
    assert r_tmp.get("grib.shortName") == meta_ref
    r_tmp = None
