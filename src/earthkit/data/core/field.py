# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import defaultdict

from earthkit.utils.array import array_namespace as eku_array_namespace
from earthkit.utils.array import convert as convert_array
from earthkit.utils.array.convert import convert_dtype

from earthkit.data.core import Base
from earthkit.data.core.order import Patch
from earthkit.data.core.order import Remapping
from earthkit.data.core.order import build_remapping
from earthkit.data.decorators import normalize
from earthkit.data.decorators import thread_safe_cached_property
from earthkit.data.utils.array import flatten as array_flatten
from earthkit.data.utils.array import reshape as array_reshape
from earthkit.data.utils.array import target_shape
from earthkit.data.utils.compute import wrap_maths
from earthkit.data.utils.metadata.args import metadata_argument_new

GRIB = "grib"

LS_KEYS = [
    "parameter.variable",
    "time.valid_datetime",
    "time.base_datetime",
    "time.step",
    "vertical.level",
    "vertical.type",
    "ensemble.member",
    "geography.grid_type",
]


# Define field component names. These are also namespace names.
DATA = "data"
TIME = "time"
PARAMETER = "parameter"
GEOGRAPHY = "geography"
VERTICAL = "vertical"
ENSEMBLE = "ensemble"
PROC = "proc"
LABELS = "labels"
METADATA = "metadata"

DUMP_ORDER = [
    PARAMETER,
    TIME,
    VERTICAL,
    ENSEMBLE,
    GEOGRAPHY,
]


class ComponentMaker:
    """A factory class to delay import of component classes."""

    def from_dict(self, name, *args, **kwargs):
        return self.default_cls(name).from_dict(*args, **kwargs)

    def from_any(self, name, *args, **kwargs):
        return self.default_cls(name).from_any(*args, **kwargs)

    def default_cls(self, name):
        return self._default_cls.get(name)

    @thread_safe_cached_property
    def _default_cls(self):
        from earthkit.data.field.data import DataFieldComponentHandler
        from earthkit.data.field.ensemble import EnsembleFieldComponentHandler
        from earthkit.data.field.geography import GeographyFieldComponentHandler
        from earthkit.data.field.labels import SimpleLabels
        from earthkit.data.field.parameter import ParameterFieldComponentHandler
        from earthkit.data.field.proc import ProcFieldComponentHandler
        from earthkit.data.field.time import TimeFieldComponentHandler
        from earthkit.data.field.vertical import VerticalFieldComponentHandler

        return {
            DATA: DataFieldComponentHandler,
            TIME: TimeFieldComponentHandler,
            PARAMETER: ParameterFieldComponentHandler,
            GEOGRAPHY: GeographyFieldComponentHandler,
            VERTICAL: VerticalFieldComponentHandler,
            ENSEMBLE: EnsembleFieldComponentHandler,
            PROC: ProcFieldComponentHandler,
            LABELS: SimpleLabels,
        }

    def empty_object(self, name):
        cls = self.default_cls(name)
        if cls is None:
            raise ValueError(f"Unknown component name: {name}")

        if name == LABELS:
            return cls()
        return cls.create_empty()


COMPONENT_MAKER = ComponentMaker()


@wrap_maths
class Field(Base):
    """A class to represent a field in Earthkit.

    A field in Earthkit is a horizontal slice of the atmosphere/hydrosphere at
    a given time.

    A Field object is composed of several components:

    - data: the data values of the field
    - time: the time of the field
    - parameter: the parameter of the field
    - geography: the geography of the field
    - vertical: the vertical level of the field
    - ensemble: the ensemble specification of the field
    - proc: the processing specification of the field
    - labels: the labels of the field

    Field is not polymorphic, but its components are.

    To create a new Field object use the factory methods such as :meth:`from_dict`
    or :meth:`from_components`.

    Parameters
    ----------
    data : DataFieldComponent
        The data of the field.
    time : TimeFieldComponent
        The time of the field.
    parameter : ParameterFieldComponent
        The parameter of the field.
    geography : GeographyFieldComponent
        The geography of the field.
    vertical : VerticalFieldComponent
        The vertical level of the field.
    ensemble : EnsembleFieldComponentHandler
        The ensemble specification of the field.
    proc : ProcFieldComponent
        The processing specification of the field.
    labels : SimpleLabels
        The labels of the field.
    **kwargs : dict
        Other keyword arguments to be passed to the Field constructor.
        These can include metadata, such as `ls_keys` for GRIB fields.

    """

    _COMPONENT_NAMES = (
        DATA,
        TIME,
        PARAMETER,
        GEOGRAPHY,
        VERTICAL,
        ENSEMBLE,
        PROC,
        LABELS,
    )

    def __init__(
        self,
        *,
        data=None,
        time=None,
        parameter=None,
        geography=None,
        vertical=None,
        ensemble=None,
        proc=None,
        labels=None,
    ):
        def _ensure(name, value):
            if value is None:
                return COMPONENT_MAKER.empty_object(name)
            return value

        self._components = {
            DATA: _ensure(DATA, data),
            TIME: _ensure(TIME, time),
            PARAMETER: _ensure(PARAMETER, parameter),
            GEOGRAPHY: _ensure(GEOGRAPHY, geography),
            VERTICAL: _ensure(VERTICAL, vertical),
            ENSEMBLE: _ensure(ENSEMBLE, ensemble),
            PROC: _ensure(PROC, proc),
            LABELS: _ensure(LABELS, labels),
        }

        self._private = dict()

    @classmethod
    def from_field(
        cls,
        field,
        data=None,
        time=None,
        parameter=None,
        geography=None,
        vertical=None,
        ensemble=None,
        proc=None,
        labels=None,
    ):
        r"""Create a Field object from another Field object.

        Parameters
        ----------
        field : Field
            The field to copy from.
        data : DataFieldComponent, dict or None
            The data of the field. When specified it is used instead of the data in
            the ``field``.
        time : Time, TimeFieldComponent, dict or None
            The time of the field. When specified it is used instead of the time
            component in the ``field``.
        parameter : Parameter, ParameterFieldComponent, dict or None
            The parameter of the field. When specified it is used instead of the
            parameter component in the ``field``.
        geography : Geography, GeographyFieldComponent, dict or None
            The geography of the field. When specified it is used instead of the geography
            component in the ``field``.
        vertical : Vertical, VerticalFieldComponent, dict or None
            The vertical level of the field. When specified it is used instead of the
            vertical component in the ``field``.
        ensemble : Ensemble, EnsembleFieldComponent, dict or None
            The ensemble specification of the field. When specified it is used instead of
            the ensemble component in the ``field``.
        proc :  Proc, ProcFieldComponent, dict or None
            The processing specification of the field. When specified it is used instead of
            the processing component in the ``field``.
        labels : SimpleLabels, dict or None
            The labels of the field. When specified it is used instead of the labels
            in the ``field``.

        Returns
        -------
        Field
            A new Field object with the components copied from the original field
            or specified in the keyword arguments.
        """
        _kwargs = {
            DATA: data,
            TIME: time,
            PARAMETER: parameter,
            GEOGRAPHY: geography,
            VERTICAL: vertical,
            ENSEMBLE: ensemble,
            PROC: proc,
            LABELS: labels,
        }

        for name in Field._COMPONENT_NAMES:
            v = _kwargs[name]
            if v is not None:
                _kwargs[name] = COMPONENT_MAKER.default_cls(name).from_any(v)
            else:
                _kwargs[name] = field._components[name]

        r = field.__class__(**_kwargs)

        # copy private data and initialize
        if field._private:
            r._private = field._private.copy()
            for v in r._private.values():
                if hasattr(v, "sync"):
                    v.sync(r)
        return r

    @classmethod
    def from_dict(cls, d):
        r"""Create a Field object from a dictionary.

        Parameters
        ----------
        d : dict
            The dictionary to create the Field from. Keys not used by any component
            are added to the labels.

        Returns
        -------
        Field
            A new Field object created from the dictionary.
        """
        if not isinstance(d, dict):
            raise TypeError("d must be a dictionary")

        return cls.from_components(**d)

        # components = {}
        # d = d.copy()

        # # TODO: add support for proc component

        # shape_hint = None

        # if "values" in d:
        #     values = d.pop("values")
        #     components[DATA] = cls._DEFAULT_PART_CLS[DATA].from_dict({"values": values})
        #     shape_hint = components[DATA].get_values(copy=False).shape

        # for name in [TIME, PARAMETER, VERTICAL, ENSEMBLE, GEOGRAPHY]:
        #     d_component = {}
        #     for k in list(d.keys()):
        #         if k.startswith(name + "."):
        #             d_component[k.split(".", 1)[1]] = d.pop(k)

        #     # geography may need shape hint from data so handled separately
        #     if name == GEOGRAPHY:
        #         components[name] = cls._DEFAULT_PART_CLS[name].from_dict(d_component, shape_hint=shape_hint)
        #     else:
        #         components[name] = cls._DEFAULT_PART_CLS[name].from_dict(d_component)

        # # geography may need shape hint from data so handled separately
        # shape_hint = None
        # if components.get(DATA):
        #     shape_hint = components[DATA].get_values(copy=False).shape

        # # d_component = {k.split(".")[1]: v for k, v in d.items() if k.startswith(GEOGRAPHY + ".")}
        # # components[GEOGRAPHY] = cls._DEFAULT_PART_CLS[GEOGRAPHY].from_dict(d, shape_hint=shape_hint)

        # # the unused items are added as labels
        # labels = SimpleLabels(d)

        # return cls(**components, labels=labels)

    @classmethod
    def from_components(
        cls,
        values=None,
        time=None,
        parameter=None,
        geography=None,
        vertical=None,
        ensemble=None,
        proc=None,
        labels=None,
    ):
        r"""Create a Field object from components.

        Parameters
        ----------
        data : DataFieldComponent, dict
            The data of the field.
        time : Time, TimeFieldComponent, dict
            The time of the field.
        parameter : Parameter, ParameterFieldComponent, dict
            parameter component in the ``field``.
        geography : Geography, GeographyFieldComponent, dict or None
            The geography of the field.
        vertical : Vertical, VerticalFieldComponent, dict or None
            The vertical level of the field.
        ensemble : Ensemble, EnsembleFieldComponent, dict or None
            The ensemble specification of the field.
        proc :  Proc, ProcFieldComponent, dict or None
            The processing specification of the field.
        labels : SimpleLabels, dict or None
            The labels of the field.

        Returns
        -------
        Field
            A new Field object with the components copied from the original field
            or specified in the keyword arguments.
        """
        _kwargs = {
            TIME: time,
            PARAMETER: parameter,
            VERTICAL: vertical,
            ENSEMBLE: ensemble,
            PROC: proc,
            LABELS: labels,
        }

        components = {}

        shape_hint = None
        if values is not None:
            components[DATA] = COMPONENT_MAKER.default_cls(DATA).from_dict({"values": values})
            shape_hint = components[DATA].get_values(copy=False).shape

        for name, v in _kwargs.items():
            if v is not None:
                component = COMPONENT_MAKER.default_cls(name).from_any(v)
                components[name] = component

        if isinstance(geography, dict):
            components[GEOGRAPHY] = COMPONENT_MAKER.default_cls(GEOGRAPHY).from_dict(
                geography, shape_hint=shape_hint
            )
        elif geography is not None:
            components[GEOGRAPHY] = COMPONENT_MAKER.default_cls(GEOGRAPHY).from_any(geography)
        return cls(**components)

    @property
    def ensemble(self):
        """Ensemble: Return the ensemble specification of the field."""
        return self._components[ENSEMBLE].component

    @property
    def time(self):
        """Time: Return the time specification of the field."""
        return self._components[TIME].component

    @property
    def vertical(self):
        """Vertical: Return the vertical specification of the field."""
        return self._components[VERTICAL].component

    @property
    def parameter(self):
        """Parameter: Return the vertical specification of the field."""
        return self._components[PARAMETER].component

    @property
    def geography(self):
        """Geography: Return the geography specification of the field."""
        return self._components[GEOGRAPHY].component

    @property
    def proc(self):
        """Proc: Return the proc specification of the field."""
        return self._components[PROC].component

    @property
    def labels(self):
        """SimpleLabels: Return the labels of the field."""
        return self._components[LABELS]

    # @classmethod
    # def from_array(cls, array):
    #     return cls.from_dict({"values": array})

    @property
    def array_namespace(self):
        r""":obj:`ArrayNamespace`: Return the array namespace of the field."""
        return eku_array_namespace(self.values)

    def free(self):
        self._components[DATA] = self._components[DATA].Offloader(self._components[DATA])

    @property
    def values(self):
        """array-like: Return the values of the field."""
        return self._components[DATA].values

    @property
    def shape(self):
        v = self.geography.shape()
        if v is not None:
            return v
        else:
            return self.values.shape

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
        v = self._components[DATA].get_values(dtype=dtype, copy=copy)
        v = convert_array(v, array_namespace="numpy")
        v = array_flatten(v) if flatten else array_reshape(v, self.shape)

        if index is not None:
            v = v[index]

        return v

    def to_array(
        self,
        flatten=False,
        dtype=None,
        copy=True,
        array_namespace=None,
        device=None,
        index=None,
    ):
        r"""Return the values stored in the field.

        Parameters
        ----------
        flatten: bool
            When it is True a flat array is returned. Otherwise an array with the field's
            :obj:`shape` is returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        array_namespace: str, array_namespace or None
            The array namespace to be used. When it is :obj:`None` the underlying array format
            of the field is used. **New in version 0.19.0**.
        device: str or None
            The device where the array will be allocated. When it is :obj:`None` the default device is used.
        index: array indexing object, optional
            The index of the values and to be extracted. When it
            is None all the values are extracted

        Returns
        -------
        array-array
            Field values.

        """
        v = self._components[DATA].get_values(dtype=dtype, copy=copy)
        if array_namespace is not None:
            v = convert_array(v, array_namespace=array_namespace, device=device)

        v = array_flatten(v) if flatten else array_reshape(v, self.shape)
        if index is not None:
            v = v[index]

        return v

    def _get_component(self, key):
        """Return the component name, component object and key name for the specified key."""
        if "." in key:
            component_name, name = key.split(".", 1)
            return component_name, self._components.get(component_name), name
        elif key in self._components[DATA]:
            return DATA, self._components[DATA], key
        return None, None, key

    def _get_single(self, key, default=None, *, astype=None, raise_on_missing=False):
        r"""Return the value for ``key``.

        Parameters
        ----------
        key: str
            Specify the metadata key to extract.
        default: value
            Specify the default value for ``key``. Returned when ``key``
            is not found and raise_on_missing is ``False``.
        astype: type as str, int or float
            Return type for ``key``. When it is supported ``astype`` is passed to the
            underlying accessor as an option. Otherwise the value is
            cast to ``astype`` after it is taken from the accessor.
        raise_on_missing: bool
            When True, raises KeyError if ``key`` is not found.

        Returns
        -------
        value
            Returns the ``key`` value. Returns ``default`` if ``key`` is not found
            and ``raise_on_missing`` is False.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and ``key`` is not found.

        """
        prefix, component, key_name = self._get_component(key)

        # first try to get the value from the component handler if it is found
        if component:
            return component.get(key_name, default=default, astype=astype, raise_on_missing=raise_on_missing)

        # handle keys like "mars.param" where "mars" is not a component but a
        # namespace in the GRIB metadata
        if prefix and prefix != METADATA:
            key_name = prefix + "." + key_name
            prefix = METADATA

        if prefix == METADATA:
            for _, private_component in self._private.items():
                if hasattr(private_component, "metadata"):
                    return private_component.metadata(
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

                    # TODO: review this
                    v = self.private_component.get(key)
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
    ):
        r"""Fast implementation of :meth:`get` for internal use.

        Parameters
        ----------
        keys: str, list or tuple
            Specify the metadata keys to extract. Can be a single key (str) or multiple
            keys as a list/tuple of str.
        default: Any, None, or a list/tuple thereof
            Specify the default value(s) for ``keys``. Returned when the given key
            is not found and ``raise_on_missing`` is False. Must have the same "structure" as ``keys``.
        astype: type as str, int or float, or a list/tuple thereof
            Return type for ``keys``. Must have the same "structure" as ``keys``.
        raise_on_missing: bool
            When True, raises KeyError if any of ``keys`` is not found.
        output: type, None
            The output type. Can be:

            - None: when ``keys`` is a str returns a single value, when ``keys`` is a list/tuple
                returns a list/tuple of values
            - list/tuple: returns a list/tuple of values. In this case ``keys`` must be a list/tuple.
            - dict: returns a dictionary with keys and their values.
        raise_on_missing: bool
            When True, raises KeyError if any of ``keys`` is not found.

        Returns
        -------
        single value, list, tuple or dict
            The values for the specified ``keys``:

            - when ``keys`` is a str returns a single value
            - when ``keys`` is a list/tuple returns a list/tuple of values when ``output``
              is None, list or tuple
            - when ``output`` is dict returns dictionary with keys and their values


        Notes
        -----
        This method assumes that the arguments have been normalized e.g. by using
        :func:`metadata_argument_new`. No checks are performed on the arguments to
        ensure that they are valid and consistent.
        """
        meth = self._get_single
        # Remapping must be an object if defined
        if remapping is not None:
            assert isinstance(remapping, (Remapping, Patch))
            meth = remapping(meth)

        if isinstance(keys, str):
            r = meth(keys, default=default, astype=astype, raise_on_missing=raise_on_missing)
            return r if output is not dict else {keys: r}
        elif isinstance(keys, (list, tuple)):
            if output is not dict:
                r = [
                    meth(k, astype=kt, default=d, raise_on_missing=raise_on_missing)
                    for k, kt, d in zip(keys, astype, default)
                ]
                return r if output is list else tuple(r)
            else:
                return {
                    k: meth(k, astype=kt, default=d, raise_on_missing=raise_on_missing)
                    for k, kt, d in zip(keys, astype, default)
                }

    def get(
        self,
        keys,
        default=None,
        *,
        astype=None,
        raise_on_missing=False,
        output=None,
        remapping=None,
        patches=None,
    ):
        r"""Return the values for the specified keys.

        Parameters
        ----------
        keys: str, list or tuple
            Specify the metadata keys to extract. Can be a single key (str) or multiple
            keys as a list/tuple of str.
        default: Any, None
            Specify the default value(s) for ``keys``. Returned when the given key
            is not found and ``raise_on_missing`` is False. When ``default`` is a single
            value, it is used for all the keys. Otherwise it must be a list/tuple of the
            same length as ``keys``.
        astype: type as str, int or float
            Return type for ``keys``.  When ``astype`` is a single type, it is used for
            all the keys. Otherwise it must be a list/tuple of the same length as ``keys``.
        raise_on_missing: bool
            When True, raises KeyError if any of ``keys`` is not found.
        output: type, None
            When None (default) returns the same type as that of ``keys``:

            - when ``keys`` is a str returns a single value
            - when ``keys`` is a list/tuple returns a list of values

            When ``output`` is dict, returns a dictionary with keys and their values.
            Other types are not supported.

        Returns
        -------
        single value, list, tuple or dict
            The values for the specified ``keys``:

            - when ``keys`` is a str returns a single value
            - when ``keys`` is a list/tuple returns a list/tuple of values
            - when ``output`` is dict returns dictionary with keys and their values.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and any of ``keys`` is not found.

        """
        if not keys:
            raise ValueError("At least one key must be specified.")

        keys, astype, default, keys_arg_type = metadata_argument_new(
            keys,
            default=default,
            astype=astype,
        )

        if output is None:
            if keys_arg_type is not str:
                output = keys_arg_type
        elif output is not dict:
            raise ValueError("output must be None or dict")

        if remapping or patches:
            remapping = build_remapping(remapping, patches, forced_build=False)

        r = self._get_fast(
            keys,
            default=default,
            astype=astype,
            raise_on_missing=raise_on_missing,
            remapping=remapping,
            output=output,
        )

        return r

    def metadata(
        self,
        keys,
        *,
        astype=None,
        output=None,
        remapping=None,
        patches=None,
    ):

        if isinstance(keys, str) and not keys.startswith("metadata."):
            keys = "metadata." + keys
        else:
            is_tuple = isinstance(keys, tuple)
            keys = ["metadata." + x for x in keys if not x.startswith("metadata.")]
            if is_tuple:
                keys = tuple(keys)

        return self.get(
            keys,
            astype=astype,
            raise_on_missing=True,
            output=output,
            remapping=remapping,
            patches=patches,
        )

    def set(self, *args, **kwargs):
        """Return a new Field with the specified metadata keys set to the given values.

        Parameters
        ----------
        *args: tuple
            Positional arguments used to specify the metadata keys and values to set. Each
            argument can be a dict with keys and values to set. When multiple dicts are given
            they are merged together with the latter dicts taking precedence over the former ones.
        **kwargs: dict, optional
            Keyword arguments used to specify the metadata keys and values to set. They take
            precedence over the positional arguments.

        Returns
        -------
        Field
            A new Field object with the specified metadata keys set to the given values.

        """
        kwargs = kwargs.copy()
        for a in args:
            if a is None:
                continue
            if isinstance(a, dict):
                kwargs.update(a)
                continue
            raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

        _kwargs = defaultdict(dict)
        for k, v in kwargs.items():
            component_name, component, key_name = self._get_component(k)
            if component is not None:
                if key_name is not None and key_name != "":
                    _kwargs[component_name][key_name] = v
                else:
                    raise KeyError(f"Key {k} cannot be set on the field.")
            else:
                raise KeyError(f"Key {k} cannot be set on the field.")
            # else:
            #     _kwargs[LABELS][k] = v

        if _kwargs:
            r = {}
            for component_name, v in _kwargs.items():
                component = self._components[component_name]
                s = component.set(**v)
                r[component_name] = s

            if r:
                return Field.from_field(self, **r)
            else:
                raise ValueError("No valid keys to set in the field.")
        return None

    def _set_values(self, array):
        data = self._components[DATA].set_values(array)
        return Field.from_field(self, data=data)

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
        # TODO: improve this to support more formats and to be more robust
        if self._get_grib():
            return "grib"
        else:
            return "dict"

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        return encoder._encode_field(self, **kwargs)

    def to_field(self, array=True):
        """Return the field itself."""
        return self

    def to_array_field(self, array_namespace=None, device=None, flatten=False, dtype=None):
        grib = self._get_grib()
        if grib is not None:
            return grib.new_array_field(
                self, array_namespace=array_namespace, device=device, flatten=flatten, dtype=dtype
            )
        return self

    def to_fieldlist(self, fields=None):
        from earthkit.data.indexing.simple import SimpleFieldList

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

    def _dump_component(self, component="all", *, filter=None, prefix_keys=False, simplify=True):
        r"""Return the components as a dict.

        Parameters
        ----------
        component: :obj:`str`, :obj:`list`, :obj:`tuple` or :obj:`all`
            The component to return. If `component` is :obj:`all`, None or empty str
            all the components will be used.

        Returns
        -------
        dict
            Each namespace is represented as a dict. When ``simplify`` is True and
            ``component`` is a str and only one namespace is available the returned dict
            contains the keys and values of that namespace. Otherwise the returned
            dict contains one item per namespace.

        Examples
        --------
        :ref:`/examples/grib_metadata.ipynb`

        See Also
        --------
        dump

        """
        if component is None or component == "":
            raise ValueError("_dump_component(): component cannot be None or empty str. Use 'all' instead.")

        if component in ["all", all, ["all"], [all]]:
            component = None

        result = {}
        for m in self._components.values():
            m.dump(self, component, result, prefix_keys=prefix_keys)

        if component and not isinstance(component, str):
            if "metadata" in component:
                component = "metadata"

        if component == "metadata" and self._private:
            md = self._private.get("metadata")
            if md and hasattr(md, "namespace"):
                md.namespace(self, filter, result, prefix_keys=prefix_keys)

        if simplify and isinstance(component, str) and len(result) == 1 and component in result:
            return result[component]

        return result

    def dump(self, component=all, filter=None, output=None, **kwargs):
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

        See Also
        --------
        namespace

        """
        from earthkit.data.utils.summary import format_namespace_dump

        d = self._dump_component(component, filter=filter, simplify=False)

        if output is dict:
            return d

        d1 = {}
        for k in DUMP_ORDER:
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

    def message(self):
        r"""Return a buffer containing the encoded message for Fields generated from a message based format (e.g. GRIB).

        Returns
        -------
        bytes
        """
        grib = self._get_grib()
        if grib is not None:
            return grib.message()
        return None

    def _set_private_data(self, name, data):
        self._private[name] = data

    def _get_private_data(self, name):
        return self._private.get(name)

    def _get_grib(self):
        if (
            self._private
            and "metadata" in self._private
            and getattr(self._private["metadata"], "NAME", None) == GRIB
        ):
            return self._private["metadata"]

        return None

    def _check(self):
        return
        # for m in self._components.values():
        #     m.check(self)

    def _get_grib_context(self, context):
        grib = self._get_grib()
        if grib is not None:
            context["handle"] = grib.handle

        for m in self._components.values():
            m.get_grib_context(context)

    @normalize("time.valid_datetime", "date")
    @normalize("time.base_datetime", "date")
    @normalize("time.forecast_reference_time", "date")
    @normalize("time.step", "timedelta")
    @normalize("base_datetime", "date")
    @normalize("valid_datetime", "date")
    @normalize("step_timedelta", "timedelta")
    @normalize("metadata.base_datetime", "date")
    @normalize("metadata.valid_datetime", "date")
    @normalize("metadata.step_timedelta", "timedelta")
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
        geography
        to_numpy
        values

        """
        _keys = dict(
            lat=self.geography.latitudes(),
            lon=self.geography.longitudes(),
            value=self.values,
        )

        if isinstance(keys, str):
            keys = [keys]

        for k in keys:
            if k not in _keys:
                raise ValueError(f"data: invalid argument: {k}")

        def _reshape(v, flatten):
            shape = target_shape(v, flatten, self.shape)
            return array_reshape(v, shape)

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
                sample = self._components[DATA].get_values(dtype=dtype)
            target_xp = eku_array_namespace(sample)
            device = target_xp.device(sample)
            target_dtype = None
            if dtype is not None:
                target_dtype = convert_dtype(dtype, target_xp)

            for k, v in ll.items():
                r[k] = convert_array(v, array_namespace=target_xp, device=device)
                if target_dtype is not None:
                    r[k] = target_xp.astype(r[k], target_dtype, copy=False)

        r = list(r.values())
        if len(r) == 1:
            return r[0]
        else:
            return eku_array_namespace(r[0]).stack(r)

    def sel(self, *args, **kwargs):
        pass

    def isel(self, *args, **kwargs):
        pass

    def order_by(self, *args, **kwargs):
        pass

    def _unary_op(self, oper):
        v = oper(self.values)
        r = self._set_values(v)
        return r

    def _binary_op(self, oper, y):
        from earthkit.data.core.fieldlist import FieldListCore
        from earthkit.data.indexing.indexed import IndexedFieldList
        from earthkit.data.wrappers import get_wrapper

        y = get_wrapper(y)
        if isinstance(y, FieldListCore):
            x = IndexedFieldList.from_fields([self])
            return x._binary_op(oper, y)

        vx = self.values
        vy = y.values
        v = oper(vx, vy)
        r = self.set(values=v)
        return r

    def __getstate__(self):
        state = {}
        state["components"] = self._components
        state["private"] = self._private
        return state

    def __setstate__(self, state):
        components = state.get("components", {})
        self.__init__(**components)
        private = state.get("private", {})
        self._private = private
