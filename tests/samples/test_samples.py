#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_sample


def test_from_sample_grib():
    ds = from_sample("storm_ophelia_wind_850.grib")
    assert len(ds) == 2
    assert ds.metadata(["param", "level"]) == [["u", 850], ["v", 850]]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
