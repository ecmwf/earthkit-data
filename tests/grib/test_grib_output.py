#!/usr/bin/env python3

# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import sys
import tempfile

import numpy as np
import pytest

import earthkit.data
from earthkit.data import from_source
from earthkit.data import to_target
from earthkit.data.core.temporary import temp_directory
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_ARRAYS  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402

EPSILON = 1e-4


def new_grib_output_compat(*args, split_output=False, **kwargs):
    from earthkit.data.targets.file import FileTarget
    from earthkit.data.targets.file_pattern import FilePatternTarget

    if split_output:
        return FilePatternTarget(*args, encoder="grib", **kwargs)
    else:
        return FileTarget(*args, encoder="grib", **kwargs)


def new_grib_coder_compat(*args, **kwargs):
    from earthkit.data.encoders.grib import GribEncoder

    return GribEncoder(*args, **kwargs)


@pytest.mark.parametrize("fl_type", FL_ARRAYS)
def test_grib_save_when_loaded_from_file_core(fl_type):
    fs, _ = load_grib_data("test6.grib", fl_type)
    assert len(fs) == 6
    with temp_file() as tmp:
        fs.to_target("file", tmp)
        fs_saved = from_source("file", tmp)
        assert len(fs) == len(fs_saved)


@pytest.mark.parametrize(
    "_kwargs,expected_value",
    [({}, 16), ({"metadata.bitsPerValue": 12}, 12), ({"bits_per_value": None}, 16)],
)
def test_grib_save_bits_per_value_fieldlist(
    _kwargs,
    expected_value,
):
    ds = from_source("file", earthkit_examples_file("test.grib"))

    with temp_file() as tmp:
        ds.to_target("file", tmp, **_kwargs)
        ds1 = from_source("file", tmp)
        assert ds1.get("metadata.bitsPerValue") == [expected_value] * len(ds)


@pytest.mark.parametrize("array", [True, False])
@pytest.mark.parametrize(
    "_kwargs,expected_value",
    [({}, 16), ({"metadata.bitsPerValue": 12}, 12)],
)
def test_grib_save_bits_per_value_single_field(array, _kwargs, expected_value):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    if array:
        ds = ds.to_fieldlist()

    with temp_file() as tmp:
        ds[0].to_target("file", tmp, **_kwargs)
        ds1 = from_source("file", tmp)
        assert ds1.get("metadata.bitsPerValue") == [expected_value]


# TODO: if we use missing_value = np.finfo(np.float32).max the test fails
@pytest.mark.parametrize("mode", ["target"])
@pytest.mark.parametrize("missing_value", [100000.0, np.finfo(np.float32).max - 1])
# @pytest.mark.parametrize("mode", ["target"])
# @pytest.mark.parametrize("missing_value", [100000.0])
def test_grib_output_missing_value_1(mode, missing_value):
    fld = from_source("file", earthkit_examples_file("test.grib"))[0]

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        values = fld.values
        values[0] = np.nan
        assert not np.isnan(values[1])

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path)
        #     f.write(values, check_nans=True, missing_value=missing_value, template=fld)
        #     f.close()
        # if mode == "compat":
        #     f = new_grib_output_compat(path)
        #     f.write(values=values, check_nans=True, missing_value=missing_value, template=fld)
        #     f.close()
        if mode == "target":
            to_target(
                "file",
                path,
                values=values,
                template=fld,
                check_nans=True,
                missing_value=missing_value,
            )
        ds = earthkit.data.from_source("file", path)
        assert ds[0].get("metadata.bitmapPresent") == 1
        assert np.isnan(ds[0].values[0])
        assert not np.isnan(values[1])


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["target"])
def test_grib_output_latlon(mode):
    data = np.random.random((181, 360))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path, date=20010101)
        #     f.write(data, param="2t")
        #     f.close()
        # elif mode == "compat":
        #     f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
        #     f.write(values=data, param="2t")
        #     f.close()
        if mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
                values=data,
            )

        ds = earthkit.data.from_source("file", path)

        assert ds[0].get("metadata.shortName") == "2t"
        assert ds[0].get("metadata.date") == 20010101
        assert ds[0].get("metadata.shortName") == "2t"
        assert ds[0].get("metadata.levtype") == "sfc"
        assert ds[0].get("metadata.edition") == 2
        assert ds[0].get("metadata.generatingProcessIdentifier") == 255

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["target"])
def test_grib_output_o96_sfc(mode):
    data = np.random.random((40320,))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path, date=20010101)
        #     f.write(data, param="2t")
        #     f.close()
        # elif mode == "compat":
        #     f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
        #     f.write(values=data, param="2t")
        #     f.close()
        if mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
                values=data,
            )

        ds = earthkit.data.from_source("file", path)

        ref = {
            "metadata.date": 20010101,
            "metadata.shortName": "2t",
            "metadata.levtype": "sfc",
            "metadata.edition": 2,
            "metadata.generatingProcessIdentifier": 255,
            "metadata.gridType": "reduced_gg",
            "metadata.N": 96,
            "metadata.isOctahedral": 1,
        }

        for k, v in ref.items():
            assert ds[0].get(k) == v, f"{k}: {ds[0].get(k)}!={v}"

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["target"])
def test_grib_output_o160_sfc(mode):
    data = np.random.random((108160,))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path, date=20010101)
        #     f.write(data, param="2t")
        #     f.close()
        # elif mode == "compat":
        #     f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
        #     f.write(values=data, param="2t")
        #     f.close()
        if mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
                values=data,
            )
        ds = earthkit.data.from_source("file", path)

        ref = {
            "metadata.date": 20010101,
            "metadata.shortName": "2t",
            "metadata.levtype": "sfc",
            "metadata.edition": 2,
            "metadata.generatingProcessIdentifier": 255,
            "metadata.gridType": "reduced_gg",
            "metadata.N": 160,
            "metadata.isOctahedral": 1,
        }

        for k, v in ref.items():
            assert ds[0].get(k) == v, f"{k}: {ds[0].get(k)}!={v}"

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["target"])
def test_grib_output_n96_sfc(mode):
    data = np.random.random(50662)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path, date=20010101)
        #     f.write(data, param="2t")
        #     f.close()
        # elif mode == "compat":
        #     f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
        #     f.write(values=data, param="2t")
        #     f.close()
        if mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
                values=data,
            )
        ds = earthkit.data.from_source("file", path)

        ref = {
            "metadata.date": 20010101,
            "metadata.shortName": "2t",
            "metadata.levtype": "sfc",
            "metadata.edition": 2,
            "metadata.generatingProcessIdentifier": 255,
            "metadata.gridType": "reduced_gg",
            "metadata.N": 96,
            "metadata.isOctahedral": 0,
        }

        for k, v in ref.items():
            assert ds[0].get(k) == v, f"{k}: {ds[0].get(k)}!={v}"

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["target"])
def test_grib_output_mars_labeling(mode):
    data = np.random.random((40320,))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path, date=20010101)
        #     f.write(data, type="fc", expver="test", step=24, param="msl")
        #     f.close()
        # elif mode == "compat":
        #     f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
        #     f.write(values=data, type="fc", expver="test", step=24, param="msl")
        #     f.close()
        if mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(
                    date=20010101,
                    generatingProcessIdentifier=255,
                    type="fc",
                    expver="test",
                    step=24,
                    param="msl",
                ),
                values=data,
            )

        ds = earthkit.data.from_source("file", path)

        assert ds[0].get("metadata.date") == 20010101
        assert ds[0].get("metadata.edition") == 2
        assert ds[0].get("metadata.step") == 24
        assert ds[0].get("metadata.step") == 24
        assert ds[0].get("metadata.expver") == "test"
        assert ds[0].get("metadata.levtype") == "sfc"
        assert ds[0].get("metadata.shortName") == "msl"
        assert ds[0].get("metadata.type") == "fc"
        assert ds[0].get("metadata.generatingProcessIdentifier") == 255
        assert ds[0].get("metadata.gridType") == "reduced_gg"
        assert ds[0].get("metadata.N") == 96
        assert ds[0].get("metadata.isOctahedral") == 1

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["target"])
@pytest.mark.parametrize("levtype", [{}, {"levtype": "pl"}])
def test_grib_output_o96_pl(mode, levtype):
    data = np.random.random((40320,))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path, date=20010101)
        #     _kwargs = dict(param="t", level=850)
        #     _kwargs.update(levtype)
        #     f.write(data, **_kwargs)
        #     f.close()
        # elif mode == "compat":
        #     f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
        #     _kwargs = dict(param="t", level=850)
        #     _kwargs.update(levtype)
        #     f.write(values=data, **_kwargs)
        #     f.close()
        if mode == "target":
            _kwargs = dict(date=20010101, generatingProcessIdentifier=255, param="t", level=850)
            _kwargs.update(levtype)
            to_target("file", path, metadata=_kwargs, values=data)

        ds = earthkit.data.from_source("file", path)

        assert ds[0].get("metadata.date") == 20010101
        assert ds[0].get("metadata.edition") == 2
        assert ds[0].get("metadata.level") == 850
        assert ds[0].get("metadata.levtype") == "pl"
        assert ds[0].get("metadata.shortName") == "t"
        assert ds[0].get("metadata.generatingProcessIdentifier") == 255
        assert ds[0].get("metadata.gridType") == "reduced_gg"
        assert ds[0].get("metadata.N") == 96
        assert ds[0].get("metadata.isOctahedral") == 1

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["target"])
@pytest.mark.parametrize("levtype", [{}, {"levtype": "pl"}])
def test_grib_output_tp(mode, levtype):
    data = np.random.random((181, 360))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path, date=20010101)
        #     # TODO: make it work for edition=2
        #     f.write(data, param="tp", step=48, edition=1)
        #     f.close()
        # elif mode == "compat":
        #     f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
        #     # TODO: make it work for edition=2
        #     f.write(values=data, param="tp", step=48, edition=1)
        #     f.close()
        if mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="tp", step=48, edition=1),
                values=data,
            )
        ds = earthkit.data.from_source("file", path)

        assert ds[0].get("metadata.date") == 20010101
        assert ds[0].get("metadata.shortName") == "tp"
        assert ds[0].get("metadata.levtype") == "sfc"
        assert ds[0].get("metadata.edition") == 1
        assert ds[0].get("metadata.step") == 48
        assert ds[0].get("metadata.step") == 48
        assert ds[0].get("metadata.generatingProcessIdentifier") == 255
        assert ds[0].get("metadata.gridType") == "regular_ll"
        assert ds[0].get("metadata.Ni") == 360
        assert ds[0].get("metadata.Nj") == 181

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("array", [True, False])
def test_grib_output_field_template(array):
    data = np.random.random((7, 12))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        ds = from_source("file", earthkit_examples_file("test6.grib"))
        if array:
            ds = ds.to_fieldlist()

        # assert ds[0].get("metadata.bitsPerValue") == 4

        path = os.path.join(tmp, "a.grib")

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path, template=ds[0], date=20010101)
        #     f.write(data, param="pt", bitsPerValue=16)
        #     f.close()
        # elif mode == "compat":
        #     f = new_grib_output_compat(
        #         path, template=ds[0], metadata=dict(date=20010101, generatingProcessIdentifier=255)
        #     )
        #     f.write(values=data, param="pt", bitsPerValue=16)
        #     f.close()

        to_target(
            "file",
            path,
            metadata=dict(date=20010101, generatingProcessIdentifier=255, param="pt", bitsPerValue=16),
            values=data,
            template=ds[0],
        )

        ds = earthkit.data.from_source("file", path)

        assert ds[0].get("metadata.date") == 20010101
        assert ds[0].get("metadata.shortName") == "pt"
        assert ds[0].get("metadata.levtype") == "pl"
        assert ds[0].get("metadata.edition") == 1
        assert ds[0].get("metadata.generatingProcessIdentifier") == 255
        assert ds[0].get("metadata.bitsPerValue") == 16

        assert np.allclose(ds[0].to_numpy(), data, rtol=1e-2, atol=1e-2)


@pytest.mark.parametrize("mode", ["target"])
@pytest.mark.parametrize(
    "pattern,expected_value",
    [
        ("{metadata.shortName}", {"t": 2, "u": 2, "v": 2}),
        (
            "{metadata.shortName}_{metadata.level}",
            {"t_1000": 1, "t_850": 1, "u_1000": 1, "u_850": 1, "v_1000": 1, "v_850": 1},
        ),
        ("{metadata.date}_{metadata.time}_{metadata.step}", {"20180801_1200_0": 6}),
        ("{metadata.date}_{metadata.time}_{metadata.step:03}", {"20180801_1200_000": 6}),
    ],
)
def test_grib_output_filename_pattern(mode, pattern, expected_value):
    ds = from_source("file", earthkit_examples_file("test6.grib"))

    with temp_directory() as tmp:
        path = os.path.join(tmp, f"{pattern}.grib")

        # if mode == "ori":
        #     f = earthkit.data.new_grib_output(path, split_output=True)
        #     for x in ds:
        #         f.write(x.values, template=x)

        #     f.close()
        # elif mode == "compat":
        #     f = new_grib_output_compat(path, split_output=True)

        #     for x in ds:
        #         f.write(values=x.values, template=x)
        #     f.close()
        if mode == "target":
            to_target(
                "file-pattern",
                path,
                data=ds,
            )

        for k, count in expected_value.items():
            path = os.path.join(tmp, f"{k}.grib")
            assert os.path.exists(path)
            assert len(from_source("file", path)) == count


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
