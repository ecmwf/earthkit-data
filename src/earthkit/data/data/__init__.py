# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, TypeAlias

from earthkit.data.core import Encodable

if TYPE_CHECKING:
    import numpy  # type: ignore[import]
    import pandas  # type: ignore[import]
    import xarray  # type: ignore[import]

    from earthkit.data.core.fieldlist import FieldList  # type: ignore[import]
    from earthkit.data.featurelist.featurelist import FeatureList  # type: ignore[import]

ArrayLike: TypeAlias = Any


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
        """Return True if this data object represents a stream.

        Returns
        -------
        bool
            True if this data object represents a stream, False otherwise.
        """
        pass

    @abstractmethod
    def describe(self) -> Any:
        """Provide a description of the data object."""
        pass

    @abstractmethod
    def to(self, to_type: Any, *args, **kwargs) -> Any:
        """Convert the data object into another type.

        Parameters
        ----------
        to_type : str or Any
            The type to convert to. It can be a str or an object that can be used to determine the target type.
            In the latter case, the object can be an earthkit-data object or an object that earthkit-data
            supports as an input. If no suitable conversion method is found, a
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
    def to_fieldlist(self, *args, **kwargs) -> "FieldList":
        """Convert into a fieldlist."""
        pass

    @abstractmethod
    def to_xarray(self, *args, **kwargs) -> "xarray.Dataset":
        """Convert into an Xarray dataset."""
        pass

    @abstractmethod
    def to_pandas(self, *args, **kwargs) -> "pandas.DataFrame":
        """Convert into a pandas dataframe."""
        pass

    @abstractmethod
    def to_geopandas(self, **kwargs):
        """Convert into a GeoPandas dataframe."""
        pass

    @abstractmethod
    def to_featurelist(self, *args, **kwargs) -> "FeatureList":
        """Convert into a list of featurelist."""
        pass

    @abstractmethod
    def to_numpy(self, *args, **kwargs) -> "numpy.ndarray":
        """Convert into a numpy array."""
        pass

    @abstractmethod
    def to_array(self, *args, **kwargs) -> ArrayLike:
        """Convert into an array-like object."""
        pass


class SimpleData(Data):
    """A simple implementation of the Data interface that provides default implementations
    for some methods.
    """

    def is_stream(self) -> bool:
        """Return False as this data object is not a stream."""
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

    def to_fieldlist(self, *args, **kwargs) -> "FieldList":
        """Convert into a fieldlist.

        This method is not implemented for this data object and raises NotImplementedError.
        """
        self._conversion_not_implemented()

    def to_xarray(self, *args, **kwargs) -> "xarray.Dataset":
        """Convert into an Xarray dataset.

        This method is not implemented for this data object and raises NotImplementedError.
        """
        self._conversion_not_implemented()

    def to_pandas(self, *args, **kwargs) -> "pandas.DataFrame":
        """Convert into a pandas dataframe.

        This method is not implemented for this data object and raises NotImplementedError.
        """
        self._conversion_not_implemented()

    def to_geopandas(self, **kwargs):
        """Convert into a GeoPandas dataframe.

        This method is not implemented for this data object and raises NotImplementedError.
        """
        self._conversion_not_implemented()

    def to_featurelist(self, *args, **kwargs):
        """Convert into a featurelist.

        This method is not implemented for this data object and raises NotImplementedError.
        """
        self._conversion_not_implemented()

    def to_numpy(self, *args, **kwargs) -> Any:
        """Convert into a numpy array.

        This method is not implemented for this data object and raises NotImplementedError.
        """
        self._conversion_not_implemented()

    def to_array(self, *args, **kwargs) -> Any:
        """Convert into an array of a given array-like type.

        This method is not implemented for this data object and raises NotImplementedError.
        """
        self._conversion_not_implemented()

    def to_value(self, *args, **kwargs) -> Any:
        """Convert into a single value.

        This method is not implemented for this data object and raises NotImplementedError.
        """
        self._conversion_not_implemented()

    def to_target(self, target, *args, **kwargs):
        """Write the data to a target.

        Parameters
        ----------
        target: str
            The target to write to. See :py:func:`to_target` for more details on the supported targets.
        *args
            Positional arguments to pass to the :func:`to_target`
        **kwargs
            Keyword arguments to pass to the :func:`to_target`. Cannot specify ``data`` in kwargs.

        See Also
        --------
        :py:func:`to_target`
        """
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
