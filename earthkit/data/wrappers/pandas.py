# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from earthkit.data.wrappers import Wrapper


class PandasSeriesWrapper(Wrapper):
    """Wrapper around a `pandas.DataFrame`, offering polymorphism and
    convenience methods.
    """

    def __init__(self, data):
        self.data = data

    def to_pandas(self):
        """
        Return a `pandas.DataFrame` representation of the data.

        Returns
        -------
        pandas.Series
        """
        return self.data
    
    

class PandasDataFrameWrapper(PandasSeriesWrapper):
    """Wrapper around a `pandas.DataFrame`, offering polymorphism and
    convenience methods.
    """

    def __init__(self, data):
        self.data = data

    def to_pandas(self):
        """
        Return a `pandas.DataFrame` representation of the data.

        Returns
        -------
        pandas.DataFrame
        """
        return self.data


def wrapper(data, *args, **kwargs):
    import pandas as pd

    if isinstance(data, pd.DataFrame):
        return PandasDataFrameWrapper(data, *args, **kwargs)
    elif isinstance(data, pd.Series):
        return PandasSeriesWrapper(data, *args, **kwargs)
    return None
