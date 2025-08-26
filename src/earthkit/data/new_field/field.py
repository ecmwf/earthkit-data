# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import defaultdict
from functools import cache

from earthkit.utils.array import array_namespace
from earthkit.utils.array import convert_array
from earthkit.utils.array import get_backend

from earthkit.data.core import Base
from earthkit.data.core.order import Remapping
from earthkit.data.core.order import build_remapping
from earthkit.data.decorators import normalize
from earthkit.data.new_field.fieldlist import SimpleFieldList
from earthkit.data.specs.data import ArrayData
from earthkit.data.utils.metadata.args import metadata_argument
from earthkit.data.utils.metadata.args import metadata_argument_new

GRIB = "grib"

LS_KEYS = [
    "name",
    "level",
    "level_type",
    "base_datetime",
    "step",
    "valid_datetime",
    "number",
    "gridType",
]


class FieldKeys:
    r"""Map keys to attributes of Field parts."""

    # PARTS = {}
    # KEYS = {}

    def __init__(self):
        from earthkit.data.specs.data import Data as data
        from earthkit.data.specs.geography import Geography as geography
        from earthkit.data.specs.parameter import Parameter as parameter
        from earthkit.data.specs.time import Time as time
        from earthkit.data.specs.vertical import Vertical as vertical

        parts = {
            "data": data,
            "time": time,
            "parameter": parameter,
            "geography": geography,
            "vertical": vertical,
        }

        self.PARTS = {}
        for k, part in parts.items():
            keys = list(part.KEYS)
            if hasattr(part, "ALIASES") and part.ALIASES:
                keys.extend(list(part.ALIASES.keys()))
            self.PARTS[k] = tuple(keys)

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

    @cache
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


class EncoderData:
    """A class to hold the encoder data."""

    def __init__(self, data=None, time=None, parameter=None, geography=None, vertical=None, labels=None):
        self.data = data
        self.time = time
        self.parameter = parameter
        self.geography = geography
        self.vertical = vertical
        self.labels = labels

    def encode(field):
        """Double dispatch to the encoder."""
        r = {}
        if hasattr(field, "handle"):
            r["handle"] = field.handle


class LazyGribField:
    def __init__(self, handle):
        self._handle = handle
        self.__field = None

    @property
    def _field(self):
        if self.__field is None:
            self.__field = Field.from_grib(self._handle)
            self._handle = None
        return self.__field

    def __getattr__(self, name):
        return getattr(self._field, name)


class Field(Base):
    """A class to represent a field in Earthkit.

    A field in Earthkit is a horizontal slice of the atmosphere/hydrosphere at
    a given time.

    A Field object is composed of several parts:
    - data: the data values of the field
    - time: the time of the field
    - parameter: the parameter of the field
    - geography: the geography of the field
    - vertical: the vertical level of the field
    - labels: the labels of the field

    Field is not polymorphic, but its parts are. To create a new Field object
    use the class methods like :meth:`from_grib`, :meth:`from_xarray`, :meth:`from_dict`, etc.

    Parameters
    ----------
    data : FieldData
        The data of the field.
    time : FieldTime
        The time of the field.
    parameter : Parameter
        The parameter of the field.
    geography : Geography
        The geography of the field.
    vertical : Vertical
        The vertical level of the field.
    labels : Labels
        The labels of the field.
    **kwargs : dict
        Other keyword arguments to be passed to the Field constructor.
        These can include metadata, such as `ls_keys` for GRIB fields.

    """

    def __init__(
        self,
        data=None,
        time=None,
        parameter=None,
        geography=None,
        vertical=None,
        labels=None,
        raw=None,
        **kwargs,
    ):
        self.data = data
        self.time = time
        self.parameter = parameter
        self.geography = geography
        self.vertical = vertical
        self.labels = labels
        self.raw = raw

        self._kwargs = kwargs

    @classmethod
    def from_field(
        cls,
        field,
        **kwargs,
    ):
        r"""Create a Field object from another Field object.

        Parameters
        ----------
        field : Field
            The field to copy from.
        **kwargs : dict
            Other keyword arguments to be passed to the Field constructor. This can include
            parts.

        Returns
        -------
        Field
            A new Field object with the data, time, parameter, geography, vertical, and labels
            copied from the original field. If any part is provided in `kwargs`, it will be
            used instead of the original part. If a part is not provided in `kwargs`, it
            will be copied from the original field.
        """
        kwargs = kwargs.copy()
        _kwargs = {}

        for name in ["data", "time", "parameter", "geography", "vertical", "labels", "raw"]:
            v = kwargs.pop(name, None)
            if v is not None:
                _kwargs[name] = v
            else:
                _kwargs[name] = getattr(field, name)

        r = cls(**_kwargs, **kwargs)

        return r

    @classmethod
    def from_grib(cls, handle, **kwargs):
        from earthkit.data.specs.data import SimpleData
        from earthkit.data.specs.geography import SimpleGeography
        from earthkit.data.specs.grib.labels import GribLabels
        from earthkit.data.specs.labels import SimpleLabels
        from earthkit.data.specs.parameter import Parameter
        from earthkit.data.specs.time import Time
        from earthkit.data.specs.vertical import Vertical

        data = SimpleData.from_grib(handle)
        parameter = Parameter.from_grib(handle)
        time = Time.from_grib(handle)
        geography = SimpleGeography.from_grib(handle)
        vertical = Vertical.from_grib(handle)
        labels = SimpleLabels()
        raw = GribLabels(handle)

        return cls(
            data=data,
            parameter=parameter,
            time=time,
            geography=geography,
            vertical=vertical,
            labels=labels,
            raw=raw,
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

    @classmethod
    def from_dict(cls, d):
        from earthkit.data.specs.data import SimpleData
        from earthkit.data.specs.geography import SimpleGeography
        from earthkit.data.specs.labels import SimpleLabels
        from earthkit.data.specs.parameter import Parameter
        from earthkit.data.specs.time import Time
        from earthkit.data.specs.vertical import Vertical

        if not isinstance(d, dict):
            raise TypeError("d must be a dictionary")

        data = SimpleData.from_dict(d)
        geography = SimpleGeography.from_dict(d)
        parameter = Parameter.from_dict(d)
        time = Time.from_dict(d)
        vertical = Vertical.from_dict(d)

        rest = {k: v for k, v in d.items() if k not in FIELD_KEYS.KEYS}

        labels = SimpleLabels(rest)

        return cls(
            data=data,
            time=time,
            parameter=parameter,
            geography=geography,
            vertical=vertical,
            labels=labels,
        )

    @property
    def array_backend(self):
        r""":obj:`ArrayBackend`: Return the array backend of the field."""
        return get_backend(self.values)

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

    def set_values(self, array):
        data = self.data.set_values(array)
        return Field.from_field(self, data=data)

    # def set_numpy(self, array):
    #     from earthkit.data.new_field.data import NumpyData

    #     return Field.from_field(self, data=NumpyData(array))

    def get_single(
        self, key, default=None, *, astype=None, raise_on_missing=False, remapping=None, patches=None
    ):
        r"""Return the value for ``key``.

        Parameters
        ----------
        key: str
            Key
        default: value
            Specify the default value for ``key``. Returned when ``key``
            is not found or its value is a missing value and raise_on_missing is ``False``.
        astype: type as str, int or float
            Return/access type for ``key``. When it is supported ``astype`` is passed to the
            underlying accessor as an option. Otherwise the value is
            cast to ``astype`` after it is taken from the accessor.
        raise_on_missing: bool
            When it is True raises an exception if ``key`` is not found or
            it has a missing value.

        Returns
        -------
        value
            Returns the ``key`` value. Returns ``default`` if ``key`` is not found
            or it has a missing value and ``raise_on_missing`` is False.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and ``key`` is not found or it has
            a missing value.

        """

        def _cast(v):
            if callable(astype):
                try:
                    return astype(v)
                except Exception:
                    return None
            return v

        remapping = build_remapping(remapping, patches, forced_build=False)
        if remapping:
            return remapping(self.get_single)(
                key, default=default, astype=astype, raise_on_missing=raise_on_missing
            )

        v = None

        # first try the parts, bar the labels/raw
        part, name = FIELD_KEYS.get(key)
        if part:
            v = getattr(getattr(self, part), name)
            return _cast(v)
        # try the labels
        elif self.labels and key in self.labels:
            v = self.labels[key]
            return _cast(v)
        # try the raw accessor
        elif self.raw:
            return self.raw.get(key, default=default, astype=astype, raise_on_missing=raise_on_missing)
        elif raise_on_missing:
            raise KeyError(f"Key {key} not found in field")

        return default

    def _get_fast(
        self,
        keys,
        default=None,
        astype=None,
        raise_on_missing=False,
        output=None,
        remapping=None,
    ):
        assert isinstance(keys, list)

        meth = self.get_single
        # Remapping must be an object if defined
        if remapping is not None:
            assert isinstance(remapping, Remapping)
            meth = remapping(meth)

        _kwargs = dict(default=default, raise_on_missing=raise_on_missing)

        if output in (list, tuple):
            if astype is None:
                r = [meth(k, **_kwargs) for k in keys]
            else:
                assert isinstance(astype, (list, tuple))
                r = [meth(k, astype=kt, **_kwargs) for k, kt in zip(keys, astype)]

            if output is tuple:
                return tuple(r)
            else:
                return r
        elif output is dict:
            if astype is None:
                return {k: meth(k, astype=astype, **_kwargs) for k in keys}
            else:
                return {k: meth(k, astype=kt, **_kwargs) for k, kt in zip(keys, astype)}
        else:
            return meth(keys[0], astype=astype, **_kwargs)

    def get(self, *keys, default=None, astype=None, raise_on_missing=False, remapping=None, patches=None):
        r"""Return the values for the specified keys.

        Parameters
        ----------
        keys: str, list or tuple
            Keys to get the values for.
        default: value
            Default value to return when a key is not found or it has a missing value.
        raise_on_missing: bool
            When it is True raises an exception if a key is not found or it has a missing value.

        Returns
        -------
        dict
            A dictionary with keys and their values.

        """
        if not keys:
            raise ValueError("At least one key must be specified.")

        keys, astype, key_arg_type = metadata_argument_new(*keys, astype=astype)
        assert isinstance(keys, list)

        remapping = build_remapping(remapping, patches, forced_build=False)

        r = self._get_fast(
            keys,
            default=default,
            astype=astype,
            raise_on_missing=raise_on_missing,
            remapping=remapping,
            output=key_arg_type,
        )

        return r

    def get_as_dict(
        self, *keys, default=None, astype=None, raise_on_missing=False, remapping=None, patches=None
    ):
        if not keys:
            raise ValueError("At least one key must be specified.")

        keys, astype, _ = metadata_argument_new(*keys, astype=astype)
        assert isinstance(keys, list)

        remapping = build_remapping(remapping, patches, forced_build=False)

        return self._get_fast(
            keys,
            default=default,
            astype=astype,
            raise_on_missing=raise_on_missing,
            remapping=remapping,
            output=dict,
        )

    def metadata(self, *keys, astype=None, remapping=None, patches=None, **kwargs):
        r"""Return metadata values from the field.

        When called without any arguments returns a :obj:`Metadata` object.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying metadata keys. Can be empty, in this case all
            the keys from the specified ``namespace`` will
            be used. (See examples below).
        astype: type name, :obj:`list` or :obj:`tuple`
            Return types for ``keys``. A single value is accepted and applied to all the ``keys``.
            Otherwise, must have same the number of elements as ``keys``. Only used when
            ``keys`` is not empty.
        remapping: dict, optional
            Creates new metadata keys from existing ones that we can refer to in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{param}{level}"}
        **kwargs: dict, optional
            Other keyword arguments:

            * namespace: :obj:`str`, :obj:`list`, :obj:`tuple`, :obj:`None` or :obj:`all`
                The namespace to choose the ``keys`` from. When ``keys`` is empty and ``namespace`` is
                :obj:`all` all the available namespaces will be used. When ``keys`` is non empty
                ``namespace`` cannot specify multiple values and it cannot be :obj:`all`. When
                ``namespace`` is None or empty str all the available keys will be used
                (without a namespace qualifier).

            * default: value, optional
                Specifies the same default value for all the ``keys`` specified. When ``default`` is
                **not present** and a key is not found or its value is a missing value
                :obj:`metadata` will raise KeyError.

        Returns
        -------
        single value, :obj:`list`, :obj:`tuple`, :obj:`dict` or :obj:`Metadata`
            - when called without any arguments returns a :obj:`Metadata` object
            - when ``keys`` is not empty:
                - returns single value when ``keys`` is a str
                - otherwise returns the same type as that of ``keys`` (:obj:`list` or :obj:`tuple`)
            - when ``keys`` is empty:
                - when ``namespace`` is None or an empty str returns a :obj:`dict` with all
                  the available keys and values
                - when ``namespace`` is :obj:`str` returns a :obj:`dict` with the keys and values
                  in that namespace
                - otherwise returns a :obj:`dict` with one item per namespace (dict of dict)

        Raises
        ------
        KeyError
            If no ``default`` is set and a key is not found in the message or it has a missing value.

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")

        Calling without arguments:

        >>> r = ds[0].metadata()
        >>> r
        <earthkit.data.readers.grib.metadata.GribMetadata object at 0x164ace170>
        >>> r["name"]
        '2 metre temperature'

        Getting keys with their native type:

        >>> ds[0].metadata("param")
        '2t'
        >>> ds[0].metadata("param", "units")
        ('2t', 'K')
        >>> ds[0].metadata(("param", "units"))
        ('2t', 'K')
        >>> ds[0].metadata(["param", "units"])
        ['2t', 'K']
        >>> ds[0].metadata(["param"])
        ['2t']
        >>> ds[0].metadata("badkey")
        KeyError: 'badkey'
        >>> ds[0].metadata("badkey", default=None)
        <BLANKLINE>

        Prescribing key types:

        >>> ds[0].metadata("centre", astype=int)
        98
        >>> ds[0].metadata(["paramId", "centre"], astype=int)
        [167, 98]
        >>> ds[0].metadata(["centre", "centre"], astype=[int, str])
        [98, 'ecmf']

        Using namespaces:

        >>> ds[0].metadata(namespace="parameter")
        {'centre': 'ecmf', 'paramId': 167, 'units': 'K', 'name': '2 metre temperature', 'shortName': '2t'}
        >>> ds[0].metadata(namespace=["parameter", "vertical"])
        {'parameter': {'centre': 'ecmf', 'paramId': 167, 'units': 'K', 'name': '2 metre temperature',
         'shortName': '2t'},
         'vertical': {'typeOfLevel': 'surface', 'level': 0}}
        >>> r = ds[0].metadata(namespace=all)
        >>> r.keys()
        dict_keys(['default', 'ls', 'geography', 'mars', 'parameter', 'statistics', 'time', 'vertical'])
        >>> r = ds[0].metadata(namespace=None)
        >>> len(r)
        186
        >>> r["name"]
        '2 metre temperature'
        """

        if remapping is not None or patches is not None:
            from earthkit.data.core.order import build_remapping

            remapping = build_remapping(remapping, patches)
            return remapping(self.metadata)(*keys, astype=astype, **kwargs)

        # when called without arguments returns the metadata object
        if len(keys) == 0 and astype is None and not kwargs:
            raise NotImplementedError("Field.metadata() without arguments is not implemented. ")
            # return self._metadata

        namespace = kwargs.pop("namespace", None)
        key, namespace, astype, key_arg_type = metadata_argument(*keys, namespace=namespace, astype=astype)

        assert isinstance(key, list)
        assert isinstance(namespace, (list, tuple))

        if key:
            assert isinstance(astype, (list, tuple))
            if namespace and namespace[0] != "default":
                key = [namespace[0] + "." + k for k in key]

            raise_on_missing = "default" not in kwargs
            default = kwargs.pop("default", None)

            r = [
                self.get(
                    k,
                    default=default,
                    astype=kt,
                    raise_on_missing=raise_on_missing,
                    **kwargs,
                )
                for k, kt in zip(key, astype)
            ]

            if key_arg_type is str:
                return r[0]
            elif key_arg_type is tuple:
                return tuple(r)
            else:
                return r
        elif namespace:
            if all in namespace:
                namespace = self._metadata.namespaces()

            r = {ns: self._metadata.as_namespace(ns) for ns in namespace}
            if len(r) == 1:
                return r[namespace[0]]
            else:
                return r
        else:
            return self._metadata.as_namespace(None)

    def set(self, **kwargs):
        _kwargs = defaultdict(dict)
        for k, v in kwargs.items():
            if callable(v):
                v = v(self, k, self)

            if self.labels and k in self.labels:
                _kwargs["labels"][k] = v
            else:
                part_name, _ = FIELD_KEYS.get(k)
                if part_name:
                    _kwargs[part_name][k] = v
                else:
                    _kwargs["labels"][k] = v

        if _kwargs:
            r = {}
            for part_name, v in _kwargs.items():
                part = getattr(self, part_name, None)
                print("set() part=", part, "v=", v)
                if part is None and part_name == "labels":
                    from earthkit.data.specs.labels import RawLabels

                    s = RawLabels(**v)
                else:
                    s = part.set(**v)
                r[part_name] = s

            print("set() result=", r)
            if r:
                return Field.from_field(self, **r)
            else:
                raise ValueError("No valid keys to set in the field.")
        return None

    # def set_step(self, step):
    #     return Field.from_field(self, time=self.time.set_step(step))

    def set_labels(self, *args, **kwargs):
        r"""Set labels for the field.

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
        if hasattr(self, "raw") and hasattr(self.raw, "handle"):
            return "grib"
        return None

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""

        # r = {}
        # for part in ["data", "time", "parameter", "geography", "vertical", "labels"]:
        #     if hasattr(self, part):
        #         r.update(self, part).to_dict(**kwargs, encoder=True)

        # r.update(kwargs)
        return encoder._encode_field(self, **kwargs)

    def grib_metadata(self):
        md = {}
        for part in ["parameter"]:
            part = getattr(self, part)
            md.update(part._to_grib(altered=True))
        return True

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

    def to_field(self, array=True):
        """Return the field itself."""
        return self

    def to_array_based(self, **kwargs):
        return deflate(self, **kwargs)

    @property
    def default_ls_keys(self):
        return LS_KEYS

    def ls(self, *args, **kwargs):
        r"""Generate a list like summary using a set of metadata keys.

        Parameters
        ----------
        *args: tuple
            Positional arguments passed to :obj:`FieldList.ls`.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`FieldList.ls`.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row.

        """
        return self.to_fieldlist().ls(*args, **kwargs)

    def load(self):
        """Load the field data."""
        data = self.data.load()
        if data is self.data:
            return self

        if self.data:
            self.data.load()
        if self.time:
            self.time.load()
        if self.parameter:
            self.parameter.load()
        if self.geography:
            self.geography.load()
        if self.vertical:
            self.vertical.load()
        if self.labels:
            self.labels.load()

    def copy(self, *, values=None, flatten=False, dtype=None, array_backend=None):
        r"""Create a new :class:`ArrayField` by copying the values and metadata.

        Parameters
        ----------
        values: array-like or None
            The values to be stored in the new :class:`Field`. When it is ``None`` the values
            extracted from the original field by using :obj:`to_array` with ``flatten``, ``dtype``
            and ``array_backend`` and copied to the new field.
        flatten: bool
            Control the shape of the values when they are extracted from the original field.
            When ``True``, flatten the array, otherwise the field's shape is kept. Only used when
            ``values`` is not provided.
        dtype: str, array.dtype or None
            Control the typecode or data-type of the values when they are extracted from
            the original field. If :obj:`None`, the default type used by the underlying
            data accessor is used. For GRIB it is ``float64``. Only used when  ``values``
            is not provided.
        array_backend: str, module or None
            Control the array backend of the values when they are extracted from
            the original field. If :obj:`None`, the underlying array format
            of the field is used. Only used when ``values`` is not provided.
        metadata: :class:`Metadata` or None
            The metadata to be stored in the new :class:`Field`. When it is :obj:`None`
            a copy of the metadata of the original field is used.

        Returns
        -------
        :class:`ArrayField`
        """
        if values is not None:
            if array_backend is not None:
                from earthkit.utils.array import convert_array

                values = convert_array(values, target_backend=array_backend)

        else:
            values = self.data.get_values(
                flatten=flatten,
                dtype=dtype,
            )

        data = ArrayData(values)

        for part in ["time", "parameter", "geography", "vertical", "labels"]:
            part_obj = getattr(self, part)
            if hasattr(part_obj, "handle"):
                part_obj = part_obj.copy()
            else:
                part_obj = part_obj.__class__(part_obj)

            setattr(data, part, part_obj)

        return Field(
            data=data,
            time=self.time,
            parameter=self.parameter,
            geography=self.geography,
            vertical=self.vertical,
            labels=self.labels,
        )

    @normalize("valid_datetime", "date")
    @normalize("base_datetime", "date")
    @normalize("forecast_reference_time", "date")
    @normalize("step", "timedelta")
    @normalize("step_range", "timedelta")
    @staticmethod
    def normalise_selection(**kwargs):
        return kwargs

    @staticmethod
    def to_fieldlist(fields):

        return SimpleFieldList.from_fields(fields)

    @property
    def grib(self):
        return self._kwargs.get("grib")

    def _data(self, keys=("lat", "lon", "value"), flatten=False, dtype=None, index=None):
        r"""Return the values and/or the geographical coordinates for each grid point.

        Parameters
        ----------
        keys: :obj:`str`, :obj:`list` or :obj:`tuple`
            Specifies the type of data to be returned. Any combination of "lat", "lon" and "value"
            is allowed here.
        flatten: bool
            When it is True a flat array per key is returned. Otherwise an array with the field's
            :obj:`shape` is returned for each key.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        index: array indexing object, optional
            The index of the values and or the latitudes/longitudes to be extracted. When it
            is None all the values and/or coordinates are extracted.

        Returns
        -------
        array-like
            An multi-dimensional array containing one array per key is returned
            (following the order in ``keys``). The underlying array format
            of the field is used. When ``keys`` is a single value only the
            array belonging to the key is returned.

        Examples
        --------
        - :ref:`/examples/grib_lat_lon_value.ipynb`

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
        >>> d = ds[0].data()
        >>> d.shape
        (3, 7, 12)
        >>> d[0, 0, 0]  # first latitude
        90.0
        >>> d[1, 0, 0]  # first longitude
        0.0
        >>> d[2, 0, 0]  # first value
        272.56417847
        >>> d = ds[0].data(keys="lon")
        >>> d.shape
        (7, 12)
        >>> d[0, 0]  # first longitude
        0.0

        See Also
        --------
        to_latlon
        to_points
        to_numpy
        values

        """
        _keys = dict(
            lat=self.geography.latitudes,
            lon=self.geography.longitudes,
            value=self.values,
        )

        if isinstance(keys, str):
            keys = [keys]

        for k in keys:
            if k not in _keys:
                raise ValueError(f"data: invalid argument: {k}")

        from earthkit.data.specs.data import SimpleData

        def _reshape(v, flatten):
            shape = SimpleData.target_shape(v, flatten, self.shape)
            return SimpleData.reshape(v, shape)

        r = {}
        for k in keys:
            # TODO: convert dtype
            # v = _keys[k](dtype=dtype)
            v = _keys[k]
            if v is None:
                raise ValueError(f"data: {k} not available")
            v = _reshape(v, flatten)
            if index is not None:
                v = v[index]
            r[k] = v

        # convert latlon to array format
        ll = {k: r[k] for k in r if k != "value"}
        if ll:
            sample = r.get("value", None)
            if sample is None:
                sample = self.data.get_values(dtype=dtype)
            for k, v in zip(ll.keys(), convert_array(list(ll.values()), target_array_sample=sample)):
                r[k] = v

        r = list(r.values())
        if len(r) == 1:
            return r[0]
        else:
            return array_namespace(r[0]).stack(r)

    def to_latlon(self, flatten=False, dtype=None, index=None):
        r"""Return the latitudes/longitudes of all the gridpoints in the field.

        Parameters
        ----------
        flatten: bool
            When it is True 1D arrays are returned. Otherwise arrays with the field's
            :obj:`shape` are returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.
        index: array indexing object, optional
            The index of the latitudes/longitudes to be extracted. When it is None
            all the values are extracted.

        Returns
        -------
        dict
            Dictionary with items "lat" and "lon", containing the arrays of the latitudes and
            longitudes, respectively. The underlying array format
            of the field is used.

        See Also
        --------
        to_points

        """
        lon, lat = self._data(("lon", "lat"), flatten=flatten, dtype=dtype, index=index)
        return dict(lat=lat, lon=lon)


class GribFieldEncoderInput:
    def __init__(self, field):
        self.field = field

    @property
    def handle(self):
        try:
            return self.field.raw.handle
        except Exception:
            return None

    def data(self, altered=True):
        values = None
        md = {}
        if not hasattr(self.field.data, "handle"):
            values = self.field.data.values

        for part in ["parameter", "vertical"]:
            part = getattr(self.field, part)
            md.update(part._to_grib(altered=True))
        return values, md


def grib_handle(field):
    for part in ["time", "parameter", "geography", "vertical", "labels"]:
        part_obj = getattr(field, part)
        if hasattr(part_obj, "handle"):
            handle = getattr(part_obj, "handle", None)
            if handle:
                return handle

    return None


def deflate(field, flatten=False, dtype=None, array_backend=None):
    if hasattr(field.data, "handle"):
        values = field.data.to_array(
            field.shape,  # type: ignore
            flatten=flatten,
            dtype=dtype,
            array_backend=array_backend,
        )
        data = ArrayData(values)
    else:
        data = field.data

    # print("data:", data)

    parts_with_handle = {}
    parts_other = {}
    handles = set()
    for part in ["time", "parameter", "geography", "vertical", "labels", "raw"]:
        part_obj = getattr(field, part)
        if hasattr(part_obj, "handle"):
            handle = getattr(part_obj, "handle", None)
            parts_with_handle[part] = (handle, part_obj)
            handles.add(handle)
        else:
            parts_other[part] = part_obj

    # print("parts_with_handle:", parts_with_handle)
    # print("parts_other:", parts_other)
    # print("handles:", handles)

    _kwargs = {}
    if len(handles) == 1:
        handle = handles.pop()
        handle = handle.deflate()
        for part, (h, part_obj) in parts_with_handle.items():
            _kwargs[part] = part_obj.__class__(h)

        if field.data is not data:
            _kwargs["data"] = data

    # print("_kwargs:", _kwargs)

    if handles == 0:
        if field.data is not data:
            _kwargs["data"] = data
    elif len(handles) > 1:
        raise ValueError("Cannot deflate field with multiple handles")

    if _kwargs:
        return Field.from_field(field, **_kwargs)
    else:
        return field
