# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_source
from earthkit.data.utils.dates import to_datetime

from . import Dataset

# from earthkit.data.utils.domains import domain_to_area


class Era5SingleLevels(Dataset):
    def __init__(self, variable, period, domain=None, time=None, grid=None):
        self.variable = variable

        request = dict(
            variable=self.variable,
            product_type="reanalysis",
        )

        # if domain is not None:
        #     request["area"] = domain_to_area(domain)

        if time is not None:
            request["time"] = time
        else:
            request["time"] = list(range(0, 24))

        if grid is not None:
            if isinstance(grid, (int, float)):
                request["grid"] = [grid, grid]
            else:
                request["grid"] = grid

        if isinstance(period, int):
            period = (period, period)

        if isinstance(period, (tuple, list)) and len(period) == 1:
            period = (period[0], period[0])

        sources = []
        for year in range(period[0], period[1] + 1):
            request["year"] = year
            request["month"] = 5
            request["day"] = 1
            print(f"request={request}")
            sources.append(
                from_source("cds", "reanalysis-era5-single-levels", **request)
            )

        self.source = from_source("multi", sources)

    def __getitem__(self, n):
        # TODO: move to superclass
        if isinstance(n, int):
            return super().__getitem__(n)

        n = to_datetime(n)
        for field in self:
            if field.datetime() == n:
                return field

        raise KeyError(n)


dataset = Era5SingleLevels
