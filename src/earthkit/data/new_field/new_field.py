# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core import Base


class FieldKeys:
    r"""Keys used to access the field attributes."""

    # PARTS = {}
    # KEYS = {}

    def __init__(self):
        from .data import Data as data
        from .geography import Geography as geography
        from .parameter import Parameter as parameter
        from .time import Time as time
        from .vertical import Vertical as vertical

        self.PARTS = {
            "data": data.KEYS,
            "time": time.KEYS,
            "parameter": parameter.KEYS,
            "geography": geography.KEYS,
            "vertical": vertical.KEYS,
        }

        self.KEYS = []
        self.SINGLE_KEYS = {}
        for part, keys in self.PARTS.items():
            if keys:
                for k in keys:
                    if k in self.KEYS:
                        raise ValueError(f"Key '{k}' already exists in FieldKeys. ")
                    self.KEYS.append(part + "." + k)
                    self.KEYS.append(k)
                    self.SINGLE_KEYS[k] = part
                    # self.SINGLE_KEYS[k + "." + k] = part

    def __contains__(self, key):
        r"""Check if the key is in the FieldKeys."""
        return key in self.KEYS

    def get(self, key):
        if key in self.KEYS:
            if key in self.SINGLE_KEYS:
                part = self.SINGLE_KEYS[key]
                name = key
            else:
                part, name = key.split(".", 1)

            print(f"key: {key} -> part: {part}, name: {name}")
            return part, name
        return None, None


FIELD_KEYS = FieldKeys()


class Field(Base):
    def __init__(
        self, data=None, time=None, parameter=None, geography=None, vertical=None, labels=None, **kwargs
    ):
        r"""Initialize a Field object."""
        self.data = data
        self.time = time
        self.parameter = parameter
        self.geography = geography
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

        for name in ["data", "time", "parameter", "geography", "vertical", "labels"]:
            v = kwargs.pop(name, None)
            if v is not None:
                _kwargs[name] = v
            else:
                _kwargs[name] = getattr(field, name)

        return cls(**_kwargs, **kwargs)

    @classmethod
    def from_grib(cls, handle, **kwargs):
        from earthkit.data.new_field.grib.grib import GribData
        from earthkit.data.new_field.grib.grib import GribGeography
        from earthkit.data.new_field.grib.grib import GribParameter
        from earthkit.data.new_field.grib.grib import GribTime
        from earthkit.data.new_field.grib.grib import GribVertical

        data = GribData(handle)
        parameter = GribParameter(handle)
        time = GribTime(handle)
        geography = GribGeography(handle)
        vertical = GribVertical(handle)

        return cls(
            data=data,
            parameter=parameter,
            time=time,
            geography=geography,
            vertical=vertical,
            **kwargs,
        )

    @classmethod
    def from_xarray(cls, variable, selection, **kwargs):
        r"""Create a Field object from an XArray field."""
        from earthkit.data.new_field.xarray.xarray import XArrayData
        from earthkit.data.new_field.xarray.xarray import XArrayGeography
        from earthkit.data.new_field.xarray.xarray import XArrayParameter
        from earthkit.data.new_field.xarray.xarray import XArrayTime
        from earthkit.data.new_field.xarray.xarray import XArrayVertical

        data = XArrayData(variable, selection)
        parameter = XArrayParameter(variable)
        time = XArrayTime(variable, selection)
        geography = XArrayGeography(variable, selection)
        vertical = XArrayVertical(variable, selection)

        return cls(
            data=data,
            parameter=parameter,
            time=time,
            geography=geography,
            vertical=vertical,
            **kwargs,
        )

    # @classmethod
    # def from_dict(cls, **kwargs):
    #     d = dict(**kwargs)
    #     data = DictData(d)
    #     time = DictTime(d)
    #     parameter = DictParameter(d)
    #     geography = DictGeography(d)
    #     vertical = DictVertical(d)
    #     labels = Labels(d)
    #     return cls(
    #         data=data,
    #         time=time,
    #         parameter=parameter,
    #         geography=geography,
    #         vertical=vertical,
    #         labels=labels,
    #     )

    @property
    def shape(self):
        return self.geography.shape

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
        return self.data.to_numpy(self.shape, flatten=flatten, dtype=dtype)

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
        array-like
            Field values.

        """
        return self.data.to_array(self.shape, flatten=flatten, dtype=dtype, array_backend=array_backend)

    def set_numpy(self, array):
        from earthkit.data.new_field.data import NumpyData

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

    def metadata(self, key, default=None):
        return self._get(key)

    def _get(self, key):
        if self.labels and key in self.labels:
            return self.labels[key]
        part, name = FIELD_KEYS.get(key)
        if part:
            part = getattr(self, part)
            if key in part.KEYS:
                return getattr(part, key)
        elif name:
            return getattr(self, name)
        else:
            raise KeyError(f"Key {key} not found in field")

    def dump(self, namespace=all, **kwargs):
        r"""Generate dump with all the metadata keys belonging to ``namespace``.

        In a Jupyter notebook it is represented as a tabbed interface.

        Parameters
        ----------
        namespace: :obj:`str`, :obj:`list`, :obj:`tuple`, :obj:`None` or :obj:`all`
            The namespace to dump. The following `namespace` values
            have a special meaning:

            - :obj:`all`: all the available namespaces will be used.
            - None or empty str: all the available keys will be used
                (without a namespace qualifier)

        **kwargs: dict, optional
            Other keyword arguments used for testing only

        Returns
        -------
        NamespaceDump
            Dict-like object with one item per namespace. In a Jupyter notebook represented
            as a tabbed interface to browse the dump contents.

        Examples
        --------
        :ref:`/examples/grib_metadata.ipynb`

        """
        from earthkit.data.utils.summary import format_namespace_dump

        if namespace is all:
            namespace = self.namespaces()
        else:
            if isinstance(namespace, str):
                namespace = [namespace]

        r = []
        for ns in namespace:
            v = self.as_namespace(ns)
            if v:
                r.append(
                    {
                        "title": ns if ns else "default",
                        "data": v,
                        "tooltip": f"Keys in the ecCodes {ns} namespace",
                    }
                )

        return format_namespace_dump(r, selected="parameter", details=self.__class__.__name__, **kwargs)
