# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from earthkit.data.sources import Source


def create_fieldlist(fields=None):
    from earthkit.data.indexing.empty import EmptyFieldList
    from earthkit.data.indexing.simple import SimpleFieldList

    if fields is None or len(fields) == 0:
        return EmptyFieldList()
    else:
        return SimpleFieldList(fields)


class FieldList(Source):
    """Base class for a FieldList.

    A FieldList is a collection of Fields. It provides methods to access the field values and metadata."""

    @abstractmethod
    def __getitem__(self, index):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @staticmethod
    def from_fields(fields=None):
        r"""Create a :class:`SimpleFieldList`.

        Parameters
        ----------
        fields: iterable, Field, None
            Iterable of :obj:`Field` objects.

        Returns
        -------
        :class:`SimpleFieldList`

        """
        return create_fieldlist(fields)

    @property
    @abstractmethod
    def values(self):
        """array-like: Get all the fields' values as a 2D array. It is formed as the array of
        :obj:`Field.values <data.core.field.Field.values>` per field.

        See Also
        --------
        to_array

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> for f in ds:
        ...     print(f.values.shape)
        ...
        (209,)
        (209,)
        >>> v = ds.values
        >>> v.shape
        (2, 209)
        >>> v[0][:3]
        array([262.78027344, 267.44726562, 268.61230469])

        """
        pass

    @abstractmethod
    def to_numpy(self, **kwargs):
        r"""Return all the fields' values as an array.

        It is formed as the array of the :obj:`data.core.field.Field.to_array` values per field.

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to :obj:`data.core.field.Field.to_array`

        Returns
        -------
        array-like
            Array containing the field values.

        See Also
        --------
        :obj:`data.core.field.Field.to_array`
        values
        to_numpy
        """
        pass

    @abstractmethod
    def to_array(self, **kwargs):
        r"""Return all the fields' values as an array.

        It is formed as the array of the :obj:`data.core.field.Field.to_array` values per field.

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to :obj:`data.core.field.Field.to_array`

        Returns
        -------
        array-like
            Array containing the field values.

        See Also
        --------
        :obj:`data.core.field.Field.to_array`
        values
        to_numpy
        """
        pass

    @abstractmethod
    def data(
        self,
        keys=("lat", "lon", "value"),
        flatten=False,
        dtype=None,
        index=None,
    ):
        r"""Return the values and/or the geographical coordinates.

        Only works when all the fields have the same grid geometry.

        Parameters
        ----------
        keys: :obj:`str`, :obj:`list` or :obj:`tuple`
            Specifies the type of data to be returned. Any combination of "lat", "lon" and "value"
            is allowed here.
        flatten: bool
            When it is True the "lat", "lon" arrays and the "value" arrays per field
            will all be flattened. Otherwise they will preserve the field's :obj:`shape`.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.
        index: array indexing object, optional
            The index of the values to be extracted from each field. When it is None all the
            values are extracted.

        Returns
        -------
        array-like
            The elements of the array (in the order of the ``keys``) are as follows:

            * the latitudes array from the first field  when "lat" is in ``keys``
            * the longitudes array from the first field when "lon" is in ``keys``
            * a values array per field when "values" is in ``keys``

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry.

        Examples
        --------
        - :ref:`/examples/grib_lat_lon_value.ipynb`

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
        >>> len(ds)
        6
        >>> d = ds.data()
        >>> d.shape
        (8, 7, 12)
        >>> d[0, 0, 0]  # first latitude
        90.0
        >>> d[1, 0, 0]  # first longitude
        0.0
        >>> d[2:, 0, 0]  # first value per field
        array([272.56417847,  -6.28688049,   7.83348083, 272.53916931,
                -4.89837646,   8.66096497])
        >>> d = ds.data(keys="lon")
        >>> d.shape
        (1, 7, 12)
        >>> d[0, 0, 0]  # first longitude
        0.0

        See Also
        --------
        geography
        to_numpy
        values

        """
        pass

    @property
    @abstractmethod
    def geography(self):
        pass

    @abstractmethod
    def get(
        self,
        keys,
        default=None,
        astype=None,
        raise_on_missing=False,
        output="auto",
        group_by_key=False,
        flatten_dict=False,
        remapping=None,
        patch=None,
    ):
        r"""Return values for the specified keys from all the fields.

        Parameters
        ----------
        keys: str, list, tuple
            Specify the field metadata keys to extract. Can be a single key (str) or multiple
            keys as a list/tuple of str. Keys are assumed to be of the form
            "component.key". For example, "time.valid_datetime" or "parameter.name". It is also allowed to specify just the component name like "time" or "parameter". In this case the corresponding component's ``to_dict()`` method is called and its result is returned. For other keys, the method looks for them in
            the private components of the fields (if any) and returns the value from the first private component that contains it.
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
        output: type, str
            Specify the output structure type in conjunction with ``group_by_key``.  When ``group_by`` is False (default) the output is a list with one item per field and ``output`` has the following effect on the items:

            - "auto" (default):
                - when ``keys`` is a str returns a single value per field
                - when ``keys`` is a list/tuple returns a list/tuple of values per field
            - list or "list": returns a list of values per field.
            - tuple or "tuple": returns a tuple of values per field.
            - dict or "dict": returns a dictionary with keys and their values per field.

            When ``group_by_key`` is True the output is grouped by key as follows and return an object with one item per key. The item contains the list of values for that key from all the fields. When ``output`` is dict a dict is returned otherwise list.

        group_by_key: bool
            When True the output is grouped by key as described in ``output``.
        flatten_dict: bool
            When True and ``output`` is dict, for each field if any of the values in the returned dict
            is itself a dict, it is flattened to depth 1 by concatenating the keys with a dot. For example, if the returned dict is ``{"a": {"x": 1, "y": 2}, "b": 3}``, it becomes ``{"a.x": 1, "a.y": 2, "b": 3}``. This option is ignored when ``output`` is not dict.
        remapping: dict, optional
            Create new metadata keys from existing ones. E.g. to define a new
            key "param_level" as the concatenated value of the "parameter.variable" and "vertical.level" keys use::

                remapping={"param_level": "{parameter.variable}{vertical.level}"}

        patch: dict, optional
            A dictionary of patch to be applied to the returned values.


        Returns
        -------
        list, dict
            The returned value depends on the ``output`` and ``group_by_key`` parameters. See above.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and any of ``keys`` is not found.


        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.get("parameter.variable")
        ['2t', 'msl']
        >>> ds.get(["parameter.variable", "parameter.units"])
        [('2t', 'K'), ('msl', 'Pa')]
        >>> ds.get(("parameter.variable", "parameter.units"))
        [['2t', 'K'], ['msl', 'Pa']]

        """
        pass

    @abstractmethod
    def metadata(self, *args, **kwargs):
        r"""Return the metadata values for each field.

        Parameters
        ----------
        *args: tuple
            Positional arguments defining the metadata keys. Passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`

        Returns
        -------
        list
            List with one item per :obj:`GribField <data.readers.grib.codes.GribField>`

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.metadata("param")
        ['2t', 'msl']
        >>> ds.metadata("param", "units")
        [('2t', 'K'), ('msl', 'Pa')]
        >>> ds.metadata(["param", "units"])
        [['2t', 'K'], ['msl', 'Pa']]

        """
        pass

    @abstractmethod
    def ls(self, n=None, keys=None, extra_keys=None, namespace=None):
        r"""Generate a list like summary using a set of metadata keys.

        Parameters
        ----------
        n: int, None
            The number of :obj:`Field`\ s to be
            listed. None means all the fields, ``n > 0`` means fields from the front, while
            ``n < 0`` means fields from the back of the fieldlist.
        keys: list of str, dict, None
            Metadata keys used when ``namespace`` is None. If ``keys`` is None the following default
            set of keys will be used:  "centre", "shortName", "typeOfLevel", "level", "dataDate",
            "dataTime", "stepRange", "dataType", "number", "gridType". To specify a column title for each
            key in the output use a dict.
        extra_keys: list of str, dict, None
            List of additional keys. To specify a column title for each key in the output
            use a dict.
        namespace: str, list of str, None
            The namespace(s) to choose the ``keys`` from. When it is set ``keys`` are omitted.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row per :obj:`Field`.

        See Also
        --------
        head
        tail

        """
        pass

    @abstractmethod
    def head(self, n=5, **kwargs):
        r"""Generate a list like summary of the first ``n`` :obj:`Field`\ s.
        Same as calling :obj:`ls` with ``n``.

        Parameters
        ----------
        n: int, None
            The number of messages (``n`` > 0) to be printed from the front.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See  :obj:`ls`.

        See Also
        --------
        ls
        tail

        Notes
        -----
        The following calls are equivalent:

        .. code-block:: python

            ds.head()
            ds.head(5)
            ds.head(n=5)
            ds.ls(5)
            ds.ls(n=5)

        """
        pass

    @abstractmethod
    def tail(self, n=5, **kwargs):
        r"""Generate a list like summary of the last ``n`` :obj:`Field`\ s.
        Same as calling :obj:`ls` with ``-n``.

        Parameters
        ----------
        n: int, None
            The number of messages (``n`` > 0)  to be printed from the back.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See  :obj:`ls`.

        See Also
        --------
        head
        ls

        Notes
        -----
        The following calls are equivalent:

        .. code-block:: python

            ds.tail()
            ds.tail(5)
            ds.tail(n=5)
            ds.ls(-5)
            ds.ls(n=-5)

        """
        pass

    @abstractmethod
    def describe(self, *args, **kwargs):
        r"""Generate a summary of the fieldlist."""
        pass

    @abstractmethod
    def unique(
        self,
        *args,
        sort=False,
        drop_none=True,
        squeeze=False,
        unwrap_single=False,
        remapping=None,
        patch=None,
        cache=True,
        progress_bar=False,
    ):
        """Return the unique values for a given set of metadata keys.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to collect unique values for.
        sort: bool, optional
            Whether to sort the collected unique values. Default is False.
        drop_none: bool, optional
            Whether to drop None values from the collected unique values. Default is True.
        squeeze: bool, optional
            When True only returns the metadata keys that have more than one values. Default is False.
        unwrap_single: bool, optional
            When True and only one metadata key is specified, the unique values are returned as a tuple instead of a dict.
            Default is False.
        remapping: dict, optional
            A dictionary for remapping keys or values during collection. Default is None.
        patch: dict, optional
            A dictionary for patching key values during collection. Default is None.
        cache: bool, optional
            Whether to use an a cache attached to the fieldlist for previously collected unique values. Default is True.
        progress_bar: bool, optional
            Whether to display a progress bar during collection. Default is False.

        Returns
        -------
        dict
            A dictionary containing the unique values for the specified metadata keys.

        """
        pass

    @abstractmethod
    def sel(self, *args, remapping=None, **kwargs) -> "FieldList":
        """Select the fields matching the given metadata conditions.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the filter condition as dict.
            (See below for details).
        remapping: dict
            Creates new metadata keys from existing ones that we can refer to in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{parameter.variable}{vertical.level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the filter conditions.
            (See below for details).

        Returns
        -------
        FieldList
            Returns a new FieldList with the filtered elements. It contains a view to the data in the
            original object, so no data is copied.

        Notes
        -----
        Filter conditions are specified by a set of metadata keys either by a dictionary (in
        ``*args``) or a set of ``**kwargs``. Both single or multiple keys are allowed to use and each
        can specify the following type of filter values:

        - single value::

            ds.sel({parameter.variable: "t"})

        - list of values::

            ds.sel({parameter.variable: ["u", "v"]})

        - slice of values (defines a closed interval, so treated as inclusive of both the start
        and stop values, unlike normal Python indexing)::

            # filter levels between 300 and 500 inclusively
            ds.sel({vertical.level: slice(300, 500)})

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> len(ds)
        18

        Selecting by a single key ("parameter.variable") with a single value:

        >>> subset = ds.sel({parameter.variable: "t"})
        >>> for f in subset:
        ...     print(f)
        ...
        Field(t,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        Field(t,700,20180801,1200,0,0)
        Field(t,500,20180801,1200,0,0)
        Field(t,400,20180801,1200,0,0)
        Field(t,300,20180801,1200,0,0)

        Selecting by multiple keys ("parameter.variable", "vertical.level") with a list and slice of values:

        >>> subset = ds.sel(
        ...     {parameter.variable: ["u", "v"], vertical.level: slice(400, 700)}
        ... )
        >>> for f in subset:
        ...     print(f)
        ...
        Field(u,700,20180801,1200,0,0)
        Field(v,700,20180801,1200,0,0)
        Field(u,500,20180801,1200,0,0)
        Field(v,500,20180801,1200,0,0)
        Field(u,400,20180801,1200,0,0)
        Field(v,400,20180801, 1200,0,0)

        Using ``remapping`` to specify the selection by a key created from two other keys
        (we created key "param_level" from "parameter.variable" and "vertical.level"):

        >>> subset = ds.sel(
        ...     param_level=["t850", "u1000"],
        ...     remapping={"param_level": "{parameter.variable}{vertical.level}"},
        ... )
        >>> for f in subset:
        ...     print(f)
        ...
        Field(u,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        """
        pass

    @abstractmethod
    def isel(self, *args, **kwargs) -> "FieldList":
        """Select the fields matching the given metadata index conditions.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the filter conditions.
            (See below for details).
        **kwargs: dict, optional
            Other keyword arguments specifying the metadata keys to perform the filtering on.
            (See below for details).

        Returns
        -------
        FieldList
            Returns a new object with the filtered elements. It contains a view to the data in
            the original object, so no data is copied.

        Notes
        -----
        :obj:`isel` works similarly to :obj:`sel` but conditions are specified by indices of metadata
        keys. A metadata index stores the unique, **sorted** values of the corresponding metadata key
        from all the fields in the input data. If the object is a
        obj:`FieldList <data.readers.grib.index.FieldList>`
        to list the indices that have more than one values use
        :meth:`FieldList.indices() <data.readers.grib.index.FieldList.indices>`, or to find
        out the values of a specific index use :meth:`FieldList.index()
        <data.readers.grib.index.FieldList.index>`.

        Filter conditions are specified by a set of **metadata** keys either by a dictionary (in
        ``*args``) or a set of ``**kwargs``. Both single or multiple keys are allowed to use and each
        can specify the following type of filter values:

        - single index::

            ds.sel({parameter.variable: 1})

        - list of indices::

            ds.sel({parameter.variable: [1, 3]})

        - **slice** of values (behaves like normal Python indexing, stop value not included)::

            # filter levels on level indices 1 and 2
            ds.sel({vertical.level: slice(1,3)})

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")

        >>> len(ds)
        18
        >>> ds.unique("parameter.variable", "vertical.level", sort=True)
        {"parameter.variable": ('t', 'u', 'v'), "vertical.level": (1000, 850, 700, 500, 400, 300)}

        >>> ds1 = ds.isel({parameter.variable: 0})
        >>> len(ds1)
        6

        >>> for f in ds1:
        ...     print(f)
        ...
        Field(t,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        Field(t,700,20180801,1200,0,0)
        Field(t,500,20180801,1200,0,0)
        Field(t,400,20180801,1200,0,0)
        Field(t,300,20180801,1200,0,0)

        >>> ds1 = ds.isel({parameter.variable: [1, 2], vertical.level: slice(2, 4)})
        >>> len(ds1)
        4

        >>> for f in ds1:
        ...     print(f)
        ...
        Field(u,700,20180801,1200,0,0)
        Field(v,700,20180801,1200,0,0)
        Field(u,500,20180801,1200,0,0)
        Field(v,500,20180801,1200,0,0)

        """
        pass

    @abstractmethod
    def order_by(self, *args, remapping=None, patch=None, **kwargs):
        """Change the order of the elements in a fieldlist.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to perform the ordering on.
            (See below for details)
        remapping: dict
            Defines new metadata keys from existing ones that we can refer to in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{param}{level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the metadata keys to perform the ordering on.
            (See below for details)

        Returns
        -------
        FieldList
            Returns a new object with reordered elements. It contains a view to the data in the
            original object, so no data is copied.

        Examples
        --------
        Ordering by a single metadata key ("parameter.variable"). The default ordering direction
        is ``ascending``:

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
        >>> for f in ds.order_by("parameter.variable"):
        ...     print(f)
        ...
        Field(t,850,20180801,1200,0,0)
        Field(t,1000,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        Field(u,1000,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)

        Ordering by multiple keys (first by "vertical.level" then by "parameter.variable"). The default ordering
        direction is ``ascending`` for both keys:

        >>> for f in ds.order_by(["vertical.level", "parameter.variable"]):
        ...     print(f)
        ...
        Field(t,850,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)
        Field(t,1000,20180801,1200,0,0)
        Field(u,1000,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)

        Specifying the ordering direction:

        >>> for f in ds.order_by(
        ...     {"parameter.variable": "ascending", "vertical.level": "descending"}
        ... ):
        ...     print(f)
        Field(t,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        Field(u,1000,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)

        Using the list of all the values of a key ("parameter.variable") to define the order:

        >>> for f in ds.order_by({"parameter.variable": ["u", "t", "v"]}):
        ...     print(f)
        Field(u,1000,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        Field(t,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)

        Using ``remapping`` to specify the order by a key created from two other keys
        (we created key "param_level" from "parameter.variable" and "vertical.level"):

        >>> ordering = ["t850", "t1000", "u1000", "v850", "v1000", "u850"]
        >>> remapping = {"param_level": "{parameter.variable}{vertical.level}"}
        >>> for f in ds.order_by({"param_level": ordering}, remapping=remapping):
        ...     print(f)
        Field(t,850,20180801,1200,0,0)
        Field(t,1000,20180801,1200,0,0)
        Field(u,1000,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        """
        pass

    @abstractmethod
    def to_fieldlist(self, array_namespace=None, device=None, **kwargs):
        r"""Convert to a new :class:`FieldList`.

        Parameters
        ----------
        array_namespace: str, array_namespace or None
            The array namespace to be used. **New in version 0.19.0**.
        device: str or None
            The device where the array will be allocated. When it is
            :obj:`None` the default device is used. **New in version 0.19.0**.
        **kwargs: dict, optional
            ``kwargs`` are passed to :obj:`to_array` to
            extract the field values the resulting object will store.

        Returns
        -------
        :class:`SimpleFieldList`
            - a new fieldlist containing :class`ArrayField` fields

        Examples
        --------
        The following example will convert a fieldlist read from a file into a
        :class:`SimpleFieldList` storing single precision field values.

        >>> import numpy as np
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.path
        'docs/examples/tuv_pl.grib'
        >>> r = ds.to_fieldlist(array_namespace="numpy", dtype=np.float32)
        >>> r
        SimpleFieldList(fields=18)
        >>> hasattr(r, "path")
        False
        >>> r.to_numpy().dtype
        dtype('float32')

        """
        pass

    # @abstractmethod
    # def to_target(self, target, **kwargs):
    #     pass

    @abstractmethod
    def to_tensor(self, *args, **kwargs):
        pass

    @abstractmethod
    def to_cube(self, *args, **kwargs):
        pass

    # @abstractmethod
    # def _default_encoder(self):
    #     pass

    @abstractmethod
    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        pass

    @abstractmethod
    def _unary_op(self, oper):
        pass

    @abstractmethod
    def _binary_op(self, oper, y):
        pass

    # @abstractmethod
    # def __getstate__(self) -> dict:
    #     """Return the state of the object for pickling."""
    #     pass

    # @abstractmethod
    # def __setstate__(self, state: dict):
    #     """Set the state of the object during unpickling."""
    #     pass

    # @abstractmethod
    # def mutate(self):
    #     pass

    # @classmethod
    # @abstractmethod
    # def merge(cls, other, **kwargs):
    #     pass
