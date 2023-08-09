#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


def test_netcdf_values_surf():
    f = from_source("file", earthkit_examples_file("test.nc"))

    eps = 1e-5

    # whole file
    v = f.values
    assert isinstance(v, np.ndarray)
    assert v.shape == (2, 209)
    v0 = v[0].flatten()
    check_array(
        v0,
        (209,),
        first=262.78027,
        last=309.62207,
        meanv=283.98642,
        eps=eps,
    )

    v1 = v[1].flatten()
    check_array(
        v1,
        (209,),
        first=101947.81,
        last=100941.875,
        meanv=101201.305,
        eps=eps,
    )

    # field
    v0_f = f[0].values
    assert isinstance(v0_f, np.ndarray)
    assert v0_f.shape == (209,)
    assert np.allclose(v0_f, v0, eps)


def test_netcdf_values_upper():
    f = from_source("file", earthkit_examples_file("tuv_pl.nc"))

    eps = 1e-5

    # whole file
    v = f.values
    assert isinstance(v, np.ndarray)
    assert v.shape == (18, 84)
    vf = v[0].flatten()
    check_array(
        vf,
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    vf = v[15].flatten()
    check_array(
        vf,
        (84,),
        first=-0.9902425,
        last=-8.989977,
        meanv=-2.037789,
        eps=eps,
    )


def test_netcdf_to_numpy_surf():
    f = from_source("file", earthkit_examples_file("test.nc"))

    eps = 1e-5
    v = f.to_numpy()
    assert isinstance(v, np.ndarray)
    assert v.shape == (2, 11, 19)

    v0 = v[0].flatten()
    check_array(
        v0,
        (209,),
        first=262.78027,
        last=309.62207,
        meanv=283.98642,
        eps=eps,
    )

    v1 = v[1].flatten()
    check_array(
        v1,
        (209,),
        first=101947.81,
        last=100941.875,
        meanv=101201.305,
        eps=eps,
    )

    # field
    v0_f = f[0].to_numpy()
    assert isinstance(v0_f, np.ndarray)
    assert v0_f.shape == (11, 19)
    assert np.allclose(v0_f.flatten(), v0, eps)


@pytest.mark.parametrize(
    "first,options, expected_shape",
    [
        (False, {}, (2, 11, 19)),
        (False, {"flatten": True}, (2, 209)),
        (False, {"flatten": False}, (2, 11, 19)),
        (True, {}, (11, 19)),
        (True, {"flatten": True}, (209,)),
        (True, {"flatten": False}, (11, 19)),
    ],
)
def test_netcdf_to_numpy_surf_shape(first, options, expected_shape):
    f = from_source("file", earthkit_examples_file("test.nc"))

    eps = 1e-5

    if first:
        data = f[0]
        v_ref = f[0].values
    else:
        data = f
        v_ref = f.values.flatten()

    v1 = data.to_numpy(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.shape == expected_shape
    v1 = v1.flatten()
    assert np.allclose(v_ref, v1, eps)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()