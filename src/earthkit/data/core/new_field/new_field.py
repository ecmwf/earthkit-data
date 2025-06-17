# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import abstractmethod

from earthkit.utils.array import array_to_numpy
from earthkit.utils.array import convert_array

from earthkit.data.core import Base


class Field(Base):
    def __init__(
        self, data=None, time=None, parameter=None, geometry=None, vertical=None, labels=None, **kwargs
    ):
        r"""Initialize a Field object."""
        self.data = data
        self.time = time
        self.parameter = parameter
        self.geometry = geometry
        self.vertical = vertical
        self.labels = labels

    @classmethod
    def from_field(
        cls,
        field,
        **kwargs,
    ):
        r"""Create a Field object from another Field object."""

        kwargs = kwargs.copy()
        _kwargs = {}

        for name in ["data", "time", "parameter", "geometry", "vertical", "labels"]:
            v = kwargs.pop(name, None)
            if v is not None:
                _kwargs[name] = v
            else:
                _kwargs[name] = getattr(field, name)

        return cls(**_kwargs, **kwargs)

    @classmethod
    def from_grib(cls, handle, **kwargs):
        from .grib import GribData
        from .grib import GribGeography
        from .grib import GribParameter
        from .grib import GribTime
        from .grib import GribVertical

        data = GribData(handle)
        parameter = GribParameter(handle)
        time = GribTime(handle)
        geometry = GribGeography(handle)
        vertical = GribVertical(handle)

        return cls(
            data=data,
            parameter=parameter,
            time=time,
            geometry=geometry,
            vertical=vertical,
            **kwargs,
        )

    # @classmethod
    # def from_dict(cls, **kwargs):
    #     d = dict(**kwargs)
    #     data = DictData(d)
    #     time = DictTime(d)
    #     parameter = DictParameter(d)
    #     geometry = DictGeography(d)
    #     vertical = DictVertical(d)
    #     labels = Labels(d)
    #     return cls(
    #         data=data,
    #         time=time,
    #         parameter=parameter,
    #         geometry=geometry,
    #         vertical=vertical,
    #         labels=labels,
    #     )

    @property
    def shape(self):
        return self.geometry.shape

    @property
    def values(self):
        """Return the values of the field."""
        return self.data.values

    def to_numpy(self, flatten=False, dtype=None):
        r"""Return the values stored in the field as an ndarray.

        Parameters
        ----------
        flatten: bool
            When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.

        Returns
        -------
        ndarray
            Field values

        """
        v = array_to_numpy(self.data.get_values(dtype=dtype))
        shape = self.data.target_shape(v, flatten, self.shape)
        return self.data.reshape(v, shape)

    def to_array(self, flatten=False, dtype=None, array_backend=None):
        r"""Return the values stored in the field.

        Parameters
        ----------
        flatten: bool
            When it is True a flat array is returned. Otherwise an array with the field's
            :obj:`shape` is returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        array_backend: str, module or None
            The array backend to be used. When it is :obj:`None` the underlying array format
            of the field is used.

        Returns
        -------
        array-array
            Field values.

        """
        v = self.data.get_values(dtype=dtype)
        if array_backend is not None:
            v = convert_array(v, target_backend=array_backend)

        shape = self.data.target_shape(v, flatten, self.shape)
        return self.data.reshape(v, shape)

    def set_numpy(self, array):
        from earthkit.data.core.new_field.data import NumpyData

        return Field.from_field(self, data=NumpyData(array))

    def set_step(self, step):
        return Field.from_field(self, time=self.time.set_step(step))

    def set_labels(self, *args, **kwargs):
        r"""Set a label for the field.

        Parameters
        ----------
        *args: tuple
            Positional arguments to be passed to the label setter.
        **kwargs: dict
            Keyword arguments to be passed to the label setter.

        Returns
        -------
        Field
            A new Field object with the updated label.
        """

        d = dict(*args, **kwargs)
        return Field(self, label=self.label.set(d))

    def to_target(self, target, *args, **kwargs):
        r"""Write the field into a target object.

        Parameters
        ----------
        target: object
            The target object to write the field into.
        *args: tuple
            Positional arguments used to specify the target object.
        **kwargs: dict, optional
            Other keyword arguments used to write the field into the target object.
        """
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def default_encoder(self):
        return self._metadata.data_format()

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        return encoder._encode_field(self, **kwargs)

    # @staticmethod
    # def create_sel(self, **kwargs):
    #     for k, v in kwargs.items():
    #         part, _, name = k.partition(".")
    #         if

    #         part = k.split(".", 1)
    #             raise ValueError(f"Unknown selection key: {k}")


def _create_handle(path, offset):
    from earthkit.data.readers.grib.codes import GribCodesReader

    return GribCodesReader.from_cache(path).at_offset(offset)


def _create_grib_field(path, offset):
    handle = _create_handle(path, offset)
    return Field.from_grib(handle)


class FieldList(Base):
    @abstractmethod
    def __getitem__(self, n):
        pass

    @abstractmethod
    def __len__(self):
        pass


class SimpleFieldList(FieldList):
    def __init__(self, fields):
        r"""Initialize a FieldList object."""
        self.fields = fields

    def append(self, field):
        self.fields.append(field)

    def __getitem__(self, n):
        return self.fields[n]

    def __len__(self):
        return len(self.fields)

    def sel(self, *args, **kwargs):
        from earthkit.data.core.select import normalize_selection

        kwargs = normalize_selection(*args, **kwargs)
        if not kwargs:
            return self

        # sel = Field.create_sel(**kwargs)

        # for field in self.fields:
        #     if not field.sel(**kwargs):
        #         return SimpleFieldList([])
