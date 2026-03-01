#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import shutil

import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.utils.testing import earthkit_examples_file
from earthkit.data.utils.testing import make_tgz
from earthkit.data.utils.testing import make_zip
from earthkit.data.utils.testing import preserve_cwd

LOG = logging.getLogger(__name__)


def test_file_source_grib():
    s = from_source("file", earthkit_examples_file("test.grib"))

    assert len(s) == 2


def test_file_source_grib_save():
    ds = from_source("file", os.path.abspath(earthkit_examples_file("test.grib")))
    with temp_directory() as tmpdir:
        # Check file save to assigned filename
        f_tmp = os.path.join(tmpdir, "test2.grib")
        ds.to_target("file", f_tmp)
        assert os.path.isfile(f_tmp)
        # Check file can be saved in current dir with detected filename:
        with preserve_cwd():
            os.chdir(tmpdir)
            ds.to_target("file")
            assert os.path.isfile("test.grib")


def test_file_source_grib_no_overwrite():
    ds = from_source("file", os.path.abspath(earthkit_examples_file("test.grib")))
    with temp_directory() as tmpdir:
        with preserve_cwd():
            os.chdir(tmpdir)
            # Save the file locally
            ds.to_target("file", "test.grib")
            # Open the local file
            ds1 = from_source("file", "test.grib")
            with pytest.warns(
                UserWarning,
                match="Earthkit refusing to overwrite",
            ):
                ds1.to_target("file", "test.grib")
            with pytest.warns(
                UserWarning,
                match="Earthkit refusing to overwrite",
            ):
                ds1.to_target("file")


def test_file_source_netcdf():
    s = from_source("file", earthkit_examples_file("test.nc"))
    assert len(s) == 2


def test_file_source_netcdf_save():
    ds = from_source("file", os.path.abspath(earthkit_examples_file("test.nc")))
    with temp_directory() as tmpdir:
        # Check file save to assigned filename
        f_tmp = os.path.join(tmpdir, "test2.nc")
        ds.to_target("file", f_tmp)
        assert os.path.isfile(f_tmp)
        # Check file can be saved in current dir with detected filename:
        with preserve_cwd():
            os.chdir(tmpdir)
            ds.to_target("file")
            assert os.path.isfile("test.nc")


def test_file_source_netcdf_no_overwrite():
    ds = from_source("file", os.path.abspath(earthkit_examples_file("test.nc")))
    with temp_directory() as tmpdir:
        with preserve_cwd():
            os.chdir(tmpdir)
            # Save the file locally
            ds.to_target("file", "test.nc")
            # Open the local file
            ds1 = from_source("file", "test.nc")
            with pytest.warns(
                UserWarning,
                match="Earthkit refusing to overwrite",
            ):
                ds1.to_target("file", "test.nc")
            with pytest.warns(
                UserWarning,
                match="Earthkit refusing to overwrite",
            ):
                ds1.to_target("file")


def test_file_source_odb():
    s = from_source("file", earthkit_examples_file("test.odb"))
    assert s.path == earthkit_examples_file("test.odb")


def test_file_glob():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    with temp_directory() as tmpdir:
        ds.to_target("file", os.path.join(tmpdir, "a.grib"))
        ds.to_target("file", os.path.join(tmpdir, "b.grib"))

        ds = from_source("file", os.path.join(tmpdir, "*.grib"))
        assert len(ds) == 4, len(ds)

        ds = from_source("file", tmpdir)
        assert len(ds) == 4, len(ds)


def test_file_single_directory():
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    with temp_directory() as tmpdir:
        s1.to_target("file", os.path.join(tmpdir, "a.grib"))
        s2.to_target("file", os.path.join(tmpdir, "b.grib"))

        ds = from_source("file", tmpdir)
        assert len(ds) == 6, len(ds)

        ref = [
            ("2t", 0),
            ("msl", 0),
            ("t", 500),
            ("z", 500),
            ("t", 850),
            ("z", 850),
        ]
        assert ds.metadata(("param", "level")) == ref


def test_file_multi_directory():
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    s3 = from_source("file", earthkit_examples_file("test6.grib"))
    with temp_directory() as tmpdir1:
        s1.to_target("file", os.path.join(tmpdir1, "a.grib"))
        s2.to_target("file", os.path.join(tmpdir1, "b.grib"))

        with temp_directory() as tmpdir2:
            s1.to_target("file", os.path.join(tmpdir2, "a.grib"))
            s3.to_target("file", os.path.join(tmpdir2, "b.grib"))

            ds = from_source("file", [tmpdir1, tmpdir2])
            assert len(ds) == 14, len(ds)

            ref = [
                ("2t", 0),
                ("msl", 0),
                ("t", 500),
                ("z", 500),
                ("t", 850),
                ("z", 850),
                ("2t", 0),
                ("msl", 0),
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
            ]

            assert ds.metadata(("param", "level")) == ref


@pytest.mark.parametrize("filter_kwarg", [(lambda x: "b.grib" in x), ("*b.grib")])
def test_file_single_directory_filter(filter_kwarg):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    with temp_directory() as tmpdir:
        s1.to_target("file", os.path.join(tmpdir, "a.grib"))
        s2.to_target("file", os.path.join(tmpdir, "b.grib"))

        ds = from_source("file", tmpdir, filter=filter_kwarg)
        assert len(ds) == 4, len(ds)

        ref = [
            ("t", 500),
            ("z", 500),
            ("t", 850),
            ("z", 850),
        ]
        assert ds.metadata(("param", "level")) == ref


@pytest.mark.parametrize("filter_kwarg", [(lambda x: "b.grib" in x), ("*b.grib")])
def test_file_multi_directory_filter(filter_kwarg):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    s3 = from_source("file", earthkit_examples_file("test6.grib"))
    with temp_directory() as tmpdir1:
        s1.to_target("file", os.path.join(tmpdir1, "a.grib"))
        s2.to_target("file", os.path.join(tmpdir1, "b.grib"))

        with temp_directory() as tmpdir2:
            s1.to_target("file", os.path.join(tmpdir2, "a.grib"))
            s3.to_target("file", os.path.join(tmpdir2, "b.grib"))

            ds = from_source("file", [tmpdir1, tmpdir2], filter=filter_kwarg)
            assert len(ds) == 10, len(ds)

            ref = [
                ("t", 500),
                ("z", 500),
                ("t", 850),
                ("z", 850),
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
            ]

            assert ds.metadata(("param", "level")) == ref


def test_file_multi_directory_with_tar():
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    s3 = from_source("file", earthkit_examples_file("test6.grib"))
    with temp_directory() as tmpdir1:
        s1.to_target("file", os.path.join(tmpdir1, "a.grib"))
        s2.to_target("file", os.path.join(tmpdir1, "b.grib"))

        with temp_directory() as tmpdir2:
            s1.to_target("file", os.path.join(tmpdir2, "a.grib"))
            s3.to_target("file", os.path.join(tmpdir2, "b.grib"))

            paths = [os.path.join(tmpdir2, f) for f in ["a.grib", "b.grib"]]
            make_tgz(tmpdir2, "test.tar.gz", paths)

            ds = from_source("file", [tmpdir1, tmpdir2])
            assert len(ds) == 22, len(ds)

            ref = [
                ("2t", 0),
                ("msl", 0),
                ("t", 500),
                ("z", 500),
                ("t", 850),
                ("z", 850),
                ("2t", 0),
                ("msl", 0),
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
                ("2t", 0),
                ("msl", 0),
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
            ]

            assert ds.get(("parameter.variable", "vertical.level")) == ref


def test_file_grib_tar_with_single_file():
    with temp_directory() as tmpdir:
        path = os.path.join(tmpdir, "a.grib")
        shutil.copy(earthkit_examples_file("test.grib"), path)
        make_tgz(tmpdir, "test.tar.gz", [path])
        t_path = os.path.join(tmpdir, "test.tar.gz")

        ds = from_source("file", t_path)
        assert len(ds) == 2, len(ds)
        assert os.path.basename(ds.path) == "a.grib"


def test_file_grib_zip_with_single_file():
    with temp_directory() as tmpdir:
        path = os.path.join(tmpdir, "a.grib")
        shutil.copy(earthkit_examples_file("test.grib"), path)
        make_zip(tmpdir, "test.zip", [path])
        t_path = os.path.join(tmpdir, "test.zip")

        ds = from_source("file", t_path)
        assert len(ds) == 2, len(ds)
        assert os.path.basename(ds.path) == "a.grib"


def test_file_netcdf_tar_with_single_file():
    with temp_directory() as tmpdir:
        path = os.path.join(tmpdir, "a.nc")
        shutil.copy(earthkit_examples_file("test.nc"), path)
        make_tgz(tmpdir, "test.tar.gz", [path])
        t_path = os.path.join(tmpdir, "test.tar.gz")

        ds = from_source("file", t_path)
        assert len(ds) == 2, len(ds)
        assert os.path.basename(ds.path) == "a.nc"


def test_file_netcdf_zip_with_single_file_1():
    with temp_directory() as tmpdir:
        path = os.path.join(tmpdir, "a.nc")
        shutil.copy(earthkit_examples_file("test.nc"), path)
        make_zip(tmpdir, "test.zip", [path])
        ar_path = os.path.join(tmpdir, "test.zip")

        ds = from_source("file", ar_path)
        assert len(ds) == 2, len(ds)
        assert os.path.basename(ds.path) == "a.nc"


def test_file_netcdf_zip_with_single_file_2():
    # This NetCDF is not read into a fieldlist
    import xarray as xr

    N = 3
    ds_in = xr.DataArray(range(N), coords={"dim_0": range(N)}, name="foo").to_dataset()
    # print(ds_in)

    with temp_directory() as tmpdir:

        path = os.path.join(tmpdir, "a.nc")
        ds_in["foo"].to_netcdf(path)

        make_zip(tmpdir, "test.zip", [path])
        z_path = os.path.join(tmpdir, "test.zip")

        ds = from_source("file", z_path)

        # print(f"{ds=}")
        assert os.path.basename(ds.path) == "a.nc"


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
