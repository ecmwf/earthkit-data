# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import abstractmethod
from typing import Any

from earthkit.data.core import Encodable


class Data(Encodable):
    """Base class for data objects in earthkit-data.

    This class defines the interface for data objects in earthkit-data. It provides methods for converting between
    different types of data objects, as well as methods for describing the data object and checking if it represents
    a stream. Subclasses of Data should implement the abstract methods defined in this class to provide specific
    functionality for different types of data.
    """

    _TYPE_NAME = None
    _FIELDLIST = "fieldlist"
    _XARRAY = "xarray"
    _PANDAS = "pandas"
    _GEOPANDAS = "geopandas"
    _FEATURELIST = "featurelist"
    _NUMPY = "numpy"
    _ARRAY = "array"
    _VALUE = "value"

    @property
    @abstractmethod
    def available_types(self) -> list[str]:
        """list[str]:  Return the list of available types that this data object can be converted to."""
        pass

    @abstractmethod
    def is_stream(self) -> bool:
        """bool: Return True if this data object represents a stream."""
        pass

    @abstractmethod
    def describe(self):
        """Provide a description of the data object."""
        pass

    @abstractmethod
    def to(self, to_type: Any, *args, **kwargs) -> Any:
        """Convert the data object into another type.

        Parameters
        ----------
        to_type : str or any
            The type to convert to. This can be a string (e.g. "fieldlist"), an earthkit-data object
            (e.g. a Data object or FieldList), or a data object that earthkit-data supports (e.g. an
            xarray dataset) that can be used to determine the target type. ``to_type``
            is used to determine the target type for conversion. If no suitable conversion method is found, a
            NotImplementedError will be raised.
        *args
            Positional arguments to pass to the conversion method.
        **kwargs
            Keyword arguments to pass to the conversion method.

        Returns
        -------
        Any
            The converted data object in the target type.

        Raises
        ------
        NotImplementedError
            If conversion to the target type is not implemented.
        """
        pass

    @abstractmethod
    def to_fieldlist(self, *args, **kwargs):
        """Convert into a fieldlist."""
        pass

    @abstractmethod
    def to_xarray(self, *args, **kwargs):
        """Convert into an Xarray dataset."""
        pass

    @abstractmethod
    def to_pandas(self, *args, **kwargs):
        """Convert into a pandas dataframe"""
        pass

    @abstractmethod
    def to_geopandas(self, **kwargs):
        """Convert into a GeoPandas dataframe."""
        pass

    @abstractmethod
    def to_featurelist(self, *args, **kwargs):
        """Convert into a list of featurelist."""
        pass

    @abstractmethod
    def to_numpy(self, *args, **kwargs):
        """Convert into a numpy array."""
        pass

    @abstractmethod
    def to_array(self, *args, **kwargs):
        """Convert into an array-like object."""
        pass


class SimpleData(Data):
    """A simple implementation of the Data interface that provides default implementations
    for some methods."""

    def is_stream(self):
        return False

    def to(self, to_type, *args, **kwargs):
        method = None
        if isinstance(to_type, str):
            type_str = to_type.lower()
            method = getattr(self, f"to_{type_str}", None)
        else:
            if isinstance(to_type, Data):
                data = to_type
            elif hasattr(to_type, "to_data_object"):
                data = to_type.to_data_object()
            else:
                from .wrappers import from_object

                data = from_object(to_type)

            if data and hasattr(data, "available_types"):
                type_str = data.available_types[0]
                method = getattr(data, f"to_{type_str}", None)

        if method is None:
            raise NotImplementedError(f"Conversion to {type_str} is not implemented")
        return method(*args, **kwargs)

    def to_fieldlist(self, *args, **kwargs):
        """Convert into a fieldlist.
        This is a default implementation that raises NotImplementedError.
        """
        self._conversion_not_implemented()

    def to_xarray(self, *args, **kwargs):
        """Convert into an Xarray dataset.
        This is a default implementation that raises NotImplementedError."""
        self._conversion_not_implemented()

    def to_pandas(self, *args, **kwargs):
        """Convert into a pandas dataframe.
        This is a default implementation that raises NotImplementedError."""
        self._conversion_not_implemented()

    def to_geopandas(self, **kwargs):
        """Convert into a GeoPandas dataframe.
        This is a default implementation that raises NotImplementedError."""
        self._conversion_not_implemented()

    def to_featurelist(self, *args, **kwargs):
        """Convert into a list of featurelist.
        This is a default implementation that raises NotImplementedError."""
        self._conversion_not_implemented()

    def to_numpy(self, *args, **kwargs):
        """Convert into a numpy array.
        This is a default implementation that raises NotImplementedError."""
        self._conversion_not_implemented()

    def to_array(self, *args, **kwargs):
        """Convert into an array-like object.
        This is a default implementation that raises NotImplementedError."""
        self._conversion_not_implemented()

    def to_values(self, *args, **kwargs):
        """Convert into a single value.
        This is a default implementation that raises NotImplementedError. Subclasses that can
        be converted to a single value should override this method."""
        self._conversion_not_implemented()

    def to_target(self, target, *args, **kwargs):
        from earthkit.data.targets import to_target

        if "data" in kwargs:
            raise ValueError("Cannot specify data in to_target when calling to_target on a data  object")
        to_target(target, *args, data=self._to_default(), **kwargs)

    def _default_encoder(self):
        if hasattr(self._source, "_default_encoder"):
            return self._source._default_encoder()
        elif hasattr(self._reader, "_default_encoder"):
            return self._reader._default_encoder()
        raise NotImplementedError("No default encoder found for this data object")

    def _encode(self, *args, **kwargs):
        return self._reader._encode(*args, **kwargs)

    def _conversion_not_implemented(self):
        import inspect

        func = inspect.stack()[1][3]
        if func.startswith("to_"):
            func = func[3:]
            txt = f"Conversion of {self._TYPE_NAME} to {func} is not implemented"
        else:
            txt = f"Conversion of {self._TYPE_NAME} with {func} is not implemented"

        raise NotImplementedError(txt)

    def _to_default(self, *args, **kwargs):
        return self.to(self.available_types[0], *args, **kwargs)
