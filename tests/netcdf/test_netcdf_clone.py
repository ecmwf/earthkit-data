#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import load_nc_or_xr_source


def test_netcdf_clone():
    """Test that a NetCDF field can cloned."""
    ds = load_nc_or_xr_source(earthkit_examples_file("test.nc"), "nc")

    field = ds[0]
    cloned_field = field.clone()

    # Test that the cloned has the expected properties equivielent to the original.
    assert field.metadata() == cloned_field.metadata()
    assert (field.data() == cloned_field.data()).all()


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
