# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.featurelist.simple import IndexFeatureListBase


class PandasList(IndexFeatureListBase):
    def __init__(self, df):
        self._df = df

    def _getitem(self, index):
        return self._df.iloc[index]

    def __len__(self):
        return len(self._df)

    # def _get_rows(self, **kwargs):
    #     return [row[1] for row in self.to_pandas(**kwargs).iterrows()]

    def ls(self, **kwargs):
        return self._df

    def head(self, n=5, **kwargs):
        return self._df.head(n, **kwargs)

    def tail(self, n=5, **kwargs):
        return self._df.tail(n, **kwargs)

    def to_pandas(self, **kwargs):
        return self._df

    def to_xarray(self, **kwargs):
        return self.to_pandas().to_xarray(**kwargs)

    def _normalise_key_values(self, **kwargs):
        return kwargs

    def describe(self, *args, **kwargs):
        pass

    def to_data_object(self):
        # TODO: to be decided what to do
        return None

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        from earthkit.data.featurelist.simple import SimpleFeatureList

        assert len(args) == 2
        fs = args[0]
        indices = list(args[1])
        return SimpleFeatureList([fs[i] for i in indices])
