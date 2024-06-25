# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

LOG = logging.getLogger(__name__)


class PandasMixIn:
    def to_pandas(self, latitude=None, longitude=None, **kwargs):
        import numpy as np
        import pandas as pd

        def ident(x):
            return x

        filter = ident

        def select_point(d):
            idx = np.where((d["lat"] == latitude) & (d["lon"] == longitude))
            return dict(lat=d["lat"][idx], lon=d["lon"][idx], value=d["value"][idx])

        if latitude is not None or longitude is not None:
            filter = select_point

        columns = ("lat", "lon", "value")
        frames = []
        for s in self:
            df = pd.DataFrame.from_dict(filter(dict(zip(columns, s.data(columns, flatten=True)))))
            df["datetime"] = s.datetime()["valid_time"]
            for k, v in s.metadata(namespace="mars").items():
                df[k] = v
            frames.append(df)
        return pd.concat(frames)
