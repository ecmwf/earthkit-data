# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from . import SimpleData


class MultiData(SimpleData):
    def __init__(self, sources):
        self.sources = sources
        # self.datas = [s._reader._to_data_object() for s in self.sources.sources]

    @property
    def available_types(self):
        types = set()
        for d in self.sources:
            types.update(d.available_types)
        return sorted(types)

    def describe(self):
        pass

    def to_fieldlist(self, *args, **kwargs):
        # return self.sources.to_fieldlist(*args, **kwargs)
        data = [s.to_data_object() for s in self.sources.sources]
        fs = [d.to_fieldlist(*args, **kwargs) for d in data]
        from earthkit.data.mergers import merge_by_class

        merged = merge_by_class(fs)
        if merged is not None:
            return merged.mutate()

        raise NotImplementedError("Conversion of MultiData to fieldlist is not implemented")

    def to_xarray(self, *args, **kwargs):
        return self.sources.to_xarray(*args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        pass

    def to_geopandas(self, *args, **kwargs):
        raise NotImplementedError("Conversion of MultiData to geopandas is not implemented")

    def to_geojson(self, *args, **kwargs):
        raise NotImplementedError("Conversion of MultiData to geojson is not implemented")

    def to_featurelist(self, *args, **kwargs):
        raise NotImplementedError("Conversion of MultiData to featurelist is not implemented")

    def to_numpy(self, *args, **kwargs):
        raise NotImplementedError("Conversion of MultiData to numpy is not implemented")

    def to_array(self, *args, **kwargs):
        raise NotImplementedError("Conversion of MultiData to array is not implemented")
