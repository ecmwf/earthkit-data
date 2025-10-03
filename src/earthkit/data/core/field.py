# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import defaultdict

import deprecation
from earthkit.utils.array import array_namespace
from earthkit.utils.array import array_to_numpy
from earthkit.utils.array import convert_array
from earthkit.utils.array import get_backend

from earthkit.data.core import Base
from earthkit.data.core.order import Patch
from earthkit.data.core.order import Remapping
from earthkit.data.core.order import build_remapping
from earthkit.data.decorators import normalize
from earthkit.data.indexing.simple import SimpleFieldList
from earthkit.data.specs.data import Data
from earthkit.data.specs.ensemble import Ensemble
from earthkit.data.specs.geography import Geography
from earthkit.data.specs.labels import Labels
from earthkit.data.specs.parameter import Parameter
from earthkit.data.specs.time import Time
from earthkit.data.specs.vertical import VerticalSpec
from earthkit.data.utils.array import reshape
from earthkit.data.utils.compute import wrap_maths
from earthkit.data.utils.metadata.args import metadata_argument
from earthkit.data.utils.metadata.args import metadata_argument_new

GRIB = "grib"

LS_KEYS = [
    "variable",
    "valid_datetime",
    "base_datetime",
    "step",
    "level",
    "level_type",
    "number",
    "grid_type",
]


def member_properties(cls):
    # members = {
    #     cls._DATA_NAME: Data,
    #     cls._TIME_NAME: Time,
    #     cls._PARAMETER_NAME: Parameter,
    #     cls._GEOGRAPHY_NAME: Geography,
    #     cls._ENSEMBLE_NAME: Ensemble,
    #     cls._VERTICAL_NAME: Vertical,
    #     cls._LABELS_NAME: Labels,
    # }

    members = [
        cls._DATA,
        cls._TIME,
        cls._PARAMETER,
        cls._GEOGRAPHY,
        cls._ENSEMBLE,
        cls._VERTICAL,
        cls._LABELS,
    ]

    # member_keys = []
    keys = {}
    for member in members:
        # print(f"member: {member['name']}")
        module = member["module"]

        for key in module.ALL_KEYS:
            # add key as a prefixed property
            method = member["name"] + "_" + key
            if getattr(cls, method, None) is None:

                def _make(prop, member):
                    def _f(self):
                        return getattr(getattr(self, f"_{member}"), prop)

                    return _f

                setattr(
                    cls,
                    method,
                    property(
                        fget=_make(key, member["name"]), doc=f"Return the {key} from .{member['name']}."
                    ),
                )

                keys[method] = (member["name"], key)
                # print(f"  add property: {method} -> {member['name']}.{key}")

            # add allow using key with dot notation
            dot_key = member["name"] + "." + key
            keys[dot_key] = (member["name"], key)

            # print(f"  add dot key: {dot_key} -> {member['name']}.{key}")

        # some module keys are added as properties without a prefix
        for key in member.get("direct", ()):
            if not hasattr(module, key):
                raise ValueError(f"Direct key {key} not found in module {module}")

            if key in keys:
                raise ValueError(f"Direct key {key} already defined in/for another member")

            if getattr(cls, key, None) is not None:
                raise ValueError(f"Direct key {key} already defined in class {cls}")

            def _make(prop, member):
                def _f(self):
                    return getattr(getattr(self, f"_{member}"), prop)

                return _f

            setattr(
                cls,
                key,
                property(fget=_make(key, member["name"]), doc=f"Return the {key} from .{member['name']}."),
            )

            keys[key] = (member["name"], key)
            # print(f"  add direct property: {key} -> {member['name']}.{key}")

    cls._MEMBER_KEYS = keys
    return cls


@member_properties
@wrap_maths
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

    _DATA = {"module": Data, "name": "data", "keys": "values"}
    _TIME = {"module": Time, "name": "time"}
    _PARAMETER = {"module": Parameter, "name": "parameter"}
    _GEOGRAPHY = {"module": Geography, "name": "geography"}
    _VERTICAL = {"module": VerticalSpec, "name": "vertical", "direct": ("level", "layer")}
    _ENSEMBLE = {"module": Ensemble, "name": "ensemble"}
    _LABELS = {"module": Labels, "name": "labels"}
    _MEMBER_KEYS = set()
    _DUMP_ORDER = ["parameter", "time", "vertical", "ensemble", "geography"]

    def __init__(
        self,
        *,
        data=None,
        time=None,
        parameter=None,
        geography=None,
        vertical=None,
        ensemble=None,
        labels=None,
    ):

        self._data = data
        self._time = time
        self._parameter = parameter
        self._geography = geography
        self._vertical = vertical
        self._ensemble = ensemble
        self._labels = labels
        self._private = dict()

        self._members = {
            self._DATA["name"]: self._data,
            self._TIME["name"]: self._time,
            self._PARAMETER["name"]: self._parameter,
            self._GEOGRAPHY["name"]: self._geography,
            self._VERTICAL["name"]: self._vertical,
            self._ENSEMBLE["name"]: self._ensemble,
            self._LABELS["name"]: self._labels,
        }

        self._check()

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

        for name in [
            Field._DATA["name"],
            Field._TIME["name"],
            Field._PARAMETER["name"],
            Field._GEOGRAPHY["name"],
            Field._VERTICAL["name"],
            Field._ENSEMBLE["name"],
            Field._LABELS["name"],
        ]:
            v = kwargs.pop(name, None)
            if v is not None:
                _kwargs[name] = v
            else:
                _kwargs[name] = getattr(field, "_" + name)

        r = field.__class__(**_kwargs, **kwargs)

        if field._private:
            r._private = field._private.copy()

        return r

    # @classmethod
    # def from_xarray(cls, variable, selection, **kwargs):
    #     r"""Create a Field object from an XArray field."""
    #     from earthkit.data.specs.data import SimpleData
    #     from earthkit.data.specs.geography import SimpleGeography
    #     from earthkit.data.specs.labels import SimpleLabels
    #     from earthkit.data.specs.parameter import Parameter
    #     from earthkit.data.specs.time import Time
    #     from earthkit.data.specs.vertical import Vertical

    #     data = SimpleData.from_xarray(variable, selection)
    #     parameter = Parameter.from_xarray(variable, selection)
    #     time = Time.from_xarray(variable, selection)
    #     geography = SimpleGeography.from_xarray(variable, selection)
    #     vertical = Vertical.from_xarray(variable, selection)
    #     labels = SimpleLabels()

    #     return cls(
    #         data=data,
    #         parameter=parameter,
    #         time=time,
    #         geography=geography,
    #         vertical=vertical,
    #         labels=labels,
    #         **kwargs,
    #     )

    @classmethod
    def from_dict(cls, d):
        from earthkit.data.specs.data import SimpleData
        from earthkit.data.specs.ensemble import SimpleEnsemble
        from earthkit.data.specs.geography import SimpleGeography
        from earthkit.data.specs.labels import SimpleLabels
        from earthkit.data.specs.parameter import SimpleParameter
        from earthkit.data.specs.time import SimpleTime
        from earthkit.data.specs.vertical import SimpleVertical

        if not isinstance(d, dict):
            raise TypeError("d must be a dictionary")

        data = SimpleData.from_dict(d)
        geography = SimpleGeography.from_dict(d, shape_hint=data.raw_values_shape)
        parameter = SimpleParameter.from_dict(d)
        time = SimpleTime.from_dict(d)
        vertical = SimpleVertical.from_dict(d)
        ensemble = SimpleEnsemble.from_dict(d)

        # the unused items are added to the labels
        rest = {k: v for k, v in d.items() if k not in cls._MEMBER_KEYS}
        labels = SimpleLabels(rest)

        return cls(
            data=data,
            time=time,
            parameter=parameter,
            geography=geography,
            vertical=vertical,
            ensemble=ensemble,
            labels=labels,
        )

    @property
    def vertical(self):
        """tuple: Return the shape of the field data."""
        return self._vertical._data

    @classmethod
    def from_array(cls, array):
        return cls.from_dict({"values": array})

    @property
    def array_backend(self):
        r""":obj:`ArrayBackend`: Return the array backend of the field."""
        return get_backend(self.values)

    def free(self):
        self.data = self.data.Offloader(self.data)

    @property
    def values(self):
        """array-like: Return the values of the field."""
        return self._data.values

    def to_numpy(self, flatten=False, dtype=None, copy=True, index=None):
        r"""Return the values stored in the field as an ndarray.

        Parameters
        ----------
        flatten: bool
            When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        index: ndarray indexing object, optional
            The index of the values and to be extracted. When it
            is None all the values are extracted

        Returns
        -------
        ndarray
            Field values

        """
        v = array_to_numpy(self._data.get_values(dtype=dtype, copy=copy, index=index))
        if flatten:
            return flatten(v)
        else:
            return reshape(v, self.shape)

    def to_array(self, flatten=False, dtype=None, copy=True, index=None, array_backend=None):
        r"""Return the values stored in the field.

        Parameters
        ----------
        flatten: bool
            When it is True a flat array is returned. Otherwise an array with the field's
            :obj:`shape` is returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        array_backend: str, module, array_namespace, :obj:`ArrayBackend` or None
            The array backend to be used. When it is :obj:`None` the underlying array format
            of the field is used.
        index: array indexing object, optional
            The index of the values and to be extracted. When it
            is None all the values are extracted

        Returns
        -------
        array-like
            Field values.

        """
        v = self._data.get_values(dtype=dtype, copy=copy, index=index)
        if array_backend is not None:
            v = convert_array(v, target_backend=array_backend)
        if flatten:
            return flatten(v)
        else:
            return reshape(v, self.shape)

    def _get_member(self, key):
        """Return the member name, member object and key name for the specified key."""
        m = self._MEMBER_KEYS.get(key)
        if m is not None:
            return m[0], self._members.get(m[0]), m[1]
        # if "." in key:
        #     member, name = key.split(".", 1)
        #     return member, self._members.get(member), name
        return None, None, None

        # if "." in key:
        #     member, name = key.split(".", 1)
        #     return member, self._members.get(member), name
        # else:
        #     for member, d in self._members.items():
        #         if key in d.ALL_KEYS:
        #             return member, d, key

        # return None, None, None

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

        remapping = build_remapping(remapping, patches, forced_build=False)
        if remapping:
            return remapping(self.get_single)(
                key, default=default, astype=astype, raise_on_missing=raise_on_missing
            )

        v = None

        # first try the members
        member_name, member, key_name = self._get_member(key)
        if member:
            v = member.get(key_name, default=default, astype=astype, raise_on_missing=raise_on_missing)
            return v
        # next try the labels with the full key
        elif key in self._labels:
            return self._labels.get(key, default=default, astype=astype, raise_on_missing=raise_on_missing)
        # try the private members
        elif self._private:
            if member_name in self._private:
                return self._private[member_name].get(
                    key_name, default=default, astype=astype, raise_on_missing=raise_on_missing
                )
            else:

                def _cast(v):
                    if callable(astype):
                        try:
                            return astype(v)
                        except Exception:
                            return None
                    return v

                v = self._private.get(key)
                if v is not None:
                    return _cast(v)

        if raise_on_missing:
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
        joiner=None,
    ):
        assert isinstance(keys, list)

        meth = self.get_single
        # Remapping must be an object if defined
        if remapping is not None:
            assert isinstance(remapping, (Remapping, Patch))
            meth = remapping(meth, joiner=joiner)

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
            if isinstance(astype, (list, tuple)):
                astype = astype[0]
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
        # collect keys to set per member
        _kwargs = defaultdict(dict)
        for k, v in kwargs.items():
            member_name, member, key_name = self._get_member(k)
            if member:
                _kwargs[member_name][key_name] = v
            else:
                _kwargs[self._LABELS_NAME][k] = v

        if _kwargs:
            r = {}
            for member_name, v in _kwargs.items():
                member = self._members[member_name]
                s = member.set(**v)
                r[member_name] = s

            if r:
                return Field.from_field(self, **r)
            else:
                raise ValueError("No valid keys to set in the field.")
        return None

    def set_values(self, array):
        data = self._data.set_values(array)
        return Field.from_field(self, data=data)

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
        return Field(self, labels=self._labels.set(d))

    @deprecation.deprecated(deprecated_in="0.13.0", details="Use to_target() instead")
    def save(self, filename, append=False, **kwargs):
        r"""Write the field into a file.

        Parameters
        ----------
        filename: str, optional
            The target file path, if not defined attempts will be made to detect the filename
        append: bool, optional
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists. Default is False
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`write`.
        """
        metadata = kwargs.pop("metadata", None)
        if metadata is None:
            metadata = {}
            bits_per_value = kwargs.pop("bits_per_value", None)
            if bits_per_value is not None:
                metadata = {"bitsPerValue": bits_per_value}
            # metadata, kwargs = _bits_per_value_to_metadata(**kwargs)
        self.to_target("file", filename, append=append, metadata=metadata, **kwargs)
        # the original implementation
        # flag = "wb" if not append else "ab"
        # with open(filename, flag) as f:
        #     self.write(f, **kwargs)

    @deprecation.deprecated(deprecated_in="0.13.0", details="Use to_target() instead")
    def write(self, f, **kwargs):
        metadata = kwargs.pop("metadata", None)
        if metadata is None:
            metadata = {}
            bits_per_value = kwargs.pop("bits_per_value", None)
            if bits_per_value is not None:
                metadata = {"bitsPerValue": bits_per_value}
            # metadata, kwargs = _bits_per_value_to_metadata(**kwargs)
        self.to_target("file", f, metadata=metadata, **kwargs)

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
        if "grib" in self._private:
            return "grib"
        return "dict"

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        return encoder._encode_field(self, **kwargs)

    def to_field(self, array=True):
        """Return the field itself."""
        return self

    def to_array_field(self, array_backend=None, flatten=False, dtype=None):
        grib = self.get_private_data("grib")
        if grib is not None:
            return grib.new_array_field(self, array_backend=array_backend, flatten=flatten, dtype=dtype)
        return self

    def to_fieldlist(self, fields=None):
        if fields is None:
            fields = [self]
        return SimpleFieldList.from_fields(fields)

    def to_xarray(self, *args, **kwargs):
        """Convert the Field into an Xarray Dataset.

        Parameters
        ----------
        *args: tuple
            Positional arguments passed to :obj:`FieldList.to_xarray`.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`FieldList.to_xarray`.

        Returns
        -------
        Xarray Dataset

        """
        return self.to_fieldlist().to_xarray(*args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        pass

    def namespace(self, name=None):
        if name is all or name is True:
            name = None

        result = {}
        for m in self._members.values():
            m.namespace(self, name, result)

        if name is not None and self._private:
            for _, v in self._private.items():
                if hasattr(v, "namespace"):
                    v.namespace(self, name, result)

        return result

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

        d = self.namespace(namespace)

        d1 = {}
        for k in self._DUMP_ORDER:
            if k in d:
                d1[k] = d.pop(k)

        d1.update(d)
        d = d1

        r = []
        for ns, v in d1.items():
            # v = self.as_namespace(ns)
            if v:
                r.append(
                    {
                        "title": ns if ns else "default",
                        "data": v,
                        "tooltip": f"Keys in the {ns} namespace",
                    }
                )

        return format_namespace_dump(r, selected="parameter", details=self.__class__.__name__, **kwargs)

    @property
    def default_ls_keys(self):
        return LS_KEYS

    def ls(self, *args, **kwargs):
        r"""Generate a list-like summary using a set of metadata keys.

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

    def head(self, *args, **kwargs):
        r"""Generate a head summary of the Field."""
        return self.to_fieldlist().head(*args, **kwargs)

    def tail(self, *args, **kwargs):
        r"""Generate a tail summary of the Field."""
        return self.to_fieldlist().tail(*args, **kwargs)

    def describe(self, *args, **kwargs):
        r"""Generate a summary of the Field."""
        return self.to_fieldlist().describe(*args, **kwargs)

    def _set_private_data(self, name, data):
        self._private[name] = data

    def get_private_data(self, name):
        return self._private.get(name)

    def _check(self):
        return
        # for m in self._members.values():
        #     m.check(self)

    def _get_grib_context(self, context):
        grib = self.get_private_data("grib")
        if grib is not None:
            context["handle"] = grib.handle

        for m in self._members.values():
            m.get_grib_context(context)

    @normalize("valid_datetime", "date")
    @normalize("base_datetime", "date")
    @normalize("forecast_reference_time", "date")
    @normalize("step", "timedelta")
    # @normalize("time_span", "timedelta")
    @staticmethod
    def normalise_key_values(**kwargs):
        r"""Normalise the selection input for :meth:`FieldList.sel`."""
        return kwargs

    def data(self, keys=("lat", "lon", "value"), flatten=False, dtype=None, index=None):
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
            lat=self._geography.latitudes,
            lon=self._geography.longitudes,
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

    def to_points(self, flatten=False, dtype=None, index=None):
        r"""Return the geographical coordinates in the data's original
        Coordinate Reference System (CRS).

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
            The index of the coordinates to be extracted. When it is None
            all the values are extracted.

        Returns
        -------
        dict
            Dictionary with items "x" and "y", containing the arrays of the x and
            y coordinates, respectively. The underlying array format
            of the field is used.

        Raises
        ------
        ValueError
            When the coordinates in the data's original CRS are not available.

        See Also
        --------
        to_latlon

        """
        from earthkit.data.specs.data import SimpleData

        def _reshape(v, flatten):
            shape = SimpleData.target_shape(v, flatten, self.shape)
            return SimpleData.reshape(v, shape)

        x = self._geography.x
        y = self._geography.y
        r = {}
        if x is not None and y is not None:
            x = _reshape(x, flatten)
            y = _reshape(y, flatten)
            if index is not None:
                x = x[index]
                y = y[index]
            r = dict(x=x, y=y)
        elif self._geography.projection.CARTOPY_CRS == "PlateCarree":
            lon, lat = self.data(("lon", "lat"), flatten=flatten, dtype=dtype, index=index)
            return dict(x=lon, y=lat)
        else:
            raise ValueError("to_points(): geographical coordinates in original CRS are not available")

        # convert values to array format
        assert r
        sample = self._values(dtype=dtype)
        for k, v in zip(r.keys(), convert_array(list(r.values()), target_array_sample=sample)):
            r[k] = v
        return r

    # def bounding_box(self):
    #     r"""Return the bounding box of the field.

    #     Returns
    #     -------
    #     :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
    #     """
    #     return self.geography.bounding_box

    def datetime(self):
        r"""Return the date and time of the field.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
        >>> ds[4].datetime()
        {'base_time': datetime.datetime(2020, 12, 21, 12, 0),
        'valid_time': datetime.datetime(2020, 12, 21, 18, 0)}

        """
        return {"base_time": self._time.base_datetime, "valid_time": self._time.valid_datetime}

    def sel(self, *args, **kwargs):
        pass

    def isel(self, *args, **kwargs):
        pass

    def order_by(self, *args, **kwargs):
        pass

    def _unary_op(self, oper):
        v = oper(self.values)
        r = self.set_values(v)
        return r

    def _binary_op(self, oper, y):
        from earthkit.data.core.fieldlist import FieldListCore
        from earthkit.data.wrappers import get_wrapper

        y = get_wrapper(y)
        if isinstance(y, FieldListCore):
            x = FieldListCore.from_fields([self])
            return x._binary_op(oper, y)

        vx = self.values
        vy = y.values
        v = oper(vx, vy)
        r = self.set_values(v)
        return r

    def __getstate__(self):
        state = {}
        state["data"] = self._data
        state["geography"] = self._geography
        state["labels"] = self._labels
        state["parameter"] = self._parameter
        state["ensemble"] = self._ensemble
        state["time"] = self._time
        state["vertical"] = self._vertical
        state["private"] = self._private
        return state

    def __setstate__(self, state):
        self.__init__(
            data=state["data"],
            geography=state["geography"],
            labels=state["labels"],
            parameter=state["parameter"],
            ensemble=state["ensemble"],
            time=state["time"],
            vertical=state["vertical"],
        )

        private = state.get("private", {})
        self._private = private
