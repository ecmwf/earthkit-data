# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import Translator


class PandasTranslator(Translator):
    """Translator class for pandas `DataFrame` and `Series`."""

    def __init__(self, data, *args, **kwargs):
        super().__init__(data.to_pandas(*args, **kwargs))


class PandasSeriesTranslator(PandasTranslator):
    """Translator class for pandas `Series`."""

    _name = "pandas.Series"

    def __call__(self):
        """Series requested, if DataFrame return the first column."""
        import pandas as pd

        if isinstance(self._data, pd.DataFrame):
            return self._data.iloc[:, 0]

        return self._data


class PandasDataFrameTranslator(PandasTranslator):
    """Translator class for pandas `DataFrame`."""

    def __call__(self):
        """Return DataFrame, if Series convert to DataFrame."""
        import pandas as pd

        if isinstance(self._data, pd.Series):
            return self._data.to_frame()

        return self._data


class GeoPandasDataFrameTranslator(PandasTranslator):
    """Translator class for geopandas `DataFrame`."""

    def __call__(self):
        """Return GeoDataFrame, if normal pandas convert to geopandas."""
        import geopandas as gpd
        import pandas as pd

        if isinstance(self._data, pd.DataFrame):
            return gpd.GeoDataFrame(self._data)

        return self._data


def translator(data, cls, *args, **kwargs):
    from earthkit.data.utils import is_module_loaded

    if not is_module_loaded("pandas"):
        return None

    import pandas as pd

    if is_module_loaded("geopandas"):
        import geopandas as gpd

        if cls in [gpd.geodataframe.GeoDataFrame]:
            return GeoPandasDataFrameTranslator(data, *args, **kwargs)

    if cls in [pd.DataFrame]:
        return PandasDataFrameTranslator(data, *args, **kwargs)
    if cls in [pd.Series]:
        return PandasSeriesTranslator(data, *args, **kwargs)

    return None
