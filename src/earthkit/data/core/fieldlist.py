# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from earthkit.data.core import Encodable
from earthkit.data.sources import Source


def create_fieldlist(fields=None):
    """Create a fieldlist object from the given fields.

    Parameters
    ----------
    fields: iterable, :class:`~earthkit.data.core.field.Field`, None
        Iterable of :class:`~earthkit.data.core.field.Field` objects. When it is None or empty,
        an empty fieldlist is returned.

    Returns
    -------
    :class:`~earthkit.data.indexing.simple.SimpleFieldList`, :class:`~earthkit.data.indexing.empty.EmptyFieldList`
        A fieldlist object containing the given fields. When ``fields`` is None or empty, an
        :class:`~earthkit.data.indexing.empty.EmptyFieldList` is returned. Otherwise a
        :class:`~earthkit.data.indexing.simple.SimpleFieldList` is returned.

    """
    from earthkit.data.indexing.empty import EmptyFieldList
    from earthkit.data.indexing.simple import SimpleFieldList

    if fields is None or len(fields) == 0:
        return EmptyFieldList()
    else:
        return SimpleFieldList(fields)


class FieldList(Source, Encodable):
    """Base class for a FieldList.

    A FieldList is a collection of Fields. It is an immutable object that provides methods to access
    the field values and metadata and allows iteration over the fields. It also provides methods to select
    a subset of fields based on their metadata.

    Implementations
    ---------------
    FieldList is an abstract class. All the concrete implementations are derived from
    :class:`~earthkit.data.indexing.indexed.IndexFieldListBase`. This class is formed by
    multiple inheritance with the :class:`~earthkit.data.core.index.Index` class that implements
    indexing capabilities without specifying the actual indexed objects. It is still an abstract
    class but provides concrete implementations for many of the FieldList methods. It also
    implements fieldlist arithmetic.

    Some of the concrete implementations are:

    - :class:`~earthkit.data.indexing.empty.EmptyFieldList` is a FieldList implementation that
      contains no fields. It can be used when building fieldlists by concatenation.
      of a FieldList with no fields. It can be used when building fieldlists by concatenation.
    - :class:`~earthkit.data.indexing.simple.SimpleFieldList`: a FieldList containing a list fields.
      Can be created from a list of fields by :obj:`from_fields` or the top
      level earthkit-data :obj:`create_fieldlist` factory function.
    - :class:`~earthkit.data.readers.grib.file.GribFieldListInFile`: a FieldList containing fields
      from a GRIB file.
    - :class:`~earthkit.data.readers.xarray.fieldlist.XArrayFieldList`: a FieldList containing fields
      from an xarray Dataset.


    Creating a FieldList
    ---------------------
    A FieldList can be created by calling the :func:`to_fieldlist` method of a high level data object,
    see :ref:`data-object` for more details.

    A :class:`~earthkit.data.indexing.simple.SimpleFieldList` can also be created directly from
    a list of fields by calling the :func:`from_fields` method, or alternatively by calling the
    top level earthkit-data :func:`create_fieldlist` factory function.
    """

    @abstractmethod
    def __getitem__(self, index):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @staticmethod
    def from_fields(fields=None):
        r"""Create a fieldlist from the given fields.

        Parameters
        ----------
        fields: iterable, :class:`~earthkit.data.core.field.Field`, None
            Iterable of :class:`~earthkit.data.core.field.Field` objects. When it is None or empty,
            an empty fieldlist is returned.

        Returns
        -------
        :class:`~earthkit.data.indexing.simple.SimpleFieldList`, :class:`~earthkit.data.indexing.empty.EmptyFieldList`
            A fieldlist object containing the given fields. When ``fields`` is None or empty, an
            :class:`~earthkit.data.indexing.empty.EmptyFieldList` is returned. Otherwise a
            :class:`~earthkit.data.indexing.simple.SimpleFieldList` is returned.

        """
        return create_fieldlist(fields)

    @property
    @abstractmethod
    def values(self):
        """Return the values of all the fields as a 2D array.

        Returns
        -------
        array-like
            Array containing the values of all the fields. The return array is
            formed as the array of the flattened values extracted from each field by
            :obj:`Field.values <earthkit.data.core.field.Field.values>`.

        See Also
        --------
        earthkit.data.core.field.Field.values
        to_array

        Examples
        --------
        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "test.grib").to_fieldlist()
        >>> for f in fl:
        ...     print(f.values.shape)
        ...
        (209,)
        (209,)
        >>> v = fl.values
        >>> v.shape
        (2, 209)
        >>> v[0][:3]
        array([262.78027344, 267.44726562, 268.61230469])

        """
        pass

    @abstractmethod
    def to_numpy(self, flatten=False, dtype=None, copy=True, index=None):
        r"""Return the values of all the fields as a Numpy array.

        Parameters
        ----------
        flatten: bool
            When it is True the values are flattened per field. Otherwise an ndarray with the field's
            :obj:`shape` is returned per field.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor of the field is used. For GRIB it is ``float64``.
        copy: bool
            When it is True a copy of the data values per field is returned. Otherwise a view
            is returned where possible.
        index: ndarray indexing object, optional
            The index of the values to be extracted per field. When it is None all the values are extracted.

        Returns
        -------
        ndarray
            Array containing the field values. It is formed as the array of values extracted by
            :obj:`earthkit.data.core.field.Field.to_numpy` per field.

        See Also
        --------
        :obj:`earthkit.data.core.field.Field.to_numpy`
        values
        to_array

        Examples
        --------
        How-to examples:

        - :ref:`/how-tos/grib/grib_array_namespace.ipynb`

        """
        pass

    @abstractmethod
    def to_array(self, **kwargs):
        r"""Return the values of all the fields as an array.

        It is formed as the array of the :obj:`earthkit.data.core.field.Field.to_array` values per field.

        Parameters
        ----------
        flatten: bool
            When it is True the values are flattened per field. Otherwise an array with the field's
            :obj:`shape` is returned per field.
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        copy: bool
            When it is True a copy of the data values per field is returned. Otherwise a view
            is returned where possible.
        array_namespace: str, array_namespace or None
            The array namespace to be used. When it is :obj:`None` the underlying array format
            of the field is used. For GRIB it is "numpy".
        device: str or None
            The device where the array will be allocated. When it is :obj:`None` the default device is used.
        index: array indexing object, optional
            The index of the values to be extracted per field. When it is None all the values are extracted.
            is None all the values are extracted.

        Returns
        -------
        array-like
            Array containing the field values. It is formed as the array of values extracted by
            :obj:`earthkit.data.core.field.Field.to_array` per field.

        See Also
        --------
        :obj:`earthkit.data.core.field.Field.to_array`
        values
        to_numpy

        Examples
        --------
        How-to examples:

        - :ref:`/how-tos/grib/grib_array_namespace.ipynb`

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


        See Also
        --------
        geography
        to_numpy
        values


        Examples
        --------
        How-to examples:

        - :ref:`/how-tos/grib/grib_lat_lon_value_ll.ipynb`
        - :ref:`/how-tos/grib/grib_lat_lon_value_rgg.ipynb`

        More examples:

        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "test6.grib").to_fieldlist()
        >>> len(fl)
        6
        >>> d = fl.data()
        >>> d.shape
        (8, 7, 12)
        >>> d[0, 0, 0]  # first latitude
        90.0
        >>> d[1, 0, 0]  # first longitude
        0.0
        >>> d[2:, 0, 0]  # first value per field
        array([272.56417847,  -6.28688049,   7.83348083, 272.53916931,
                -4.89837646,   8.66096497])
        >>> d = fl.data(keys="lon")
        >>> d.shape
        (1, 7, 12)
        >>> d[0, 0, 0]  # first longitude
        0.0

        """
        pass

    @property
    @abstractmethod
    def geography(self):
        """Return the geography of the FieldList.

        Returns
        -------
        GeographyBase
            If the fields in the FieldList have the same grid geometry, the returned geography is the one of
            the first field. Otherwise an error is raised.

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry or the FieldList is empty.
        """
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
            "component.key". For example, "time.valid_datetime" or "parameter.name". Keys from the
            raw field metadata (if any) can be accessed using the "metadata.key" syntax.
            For example, when a :obj:`Field` was created from a GRIB message, the ecCodes GRIB keys can
            be accessed as "metadata.shortName" or "metadata.level".
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
            Specify the output structure type in conjunction with ``group_by_key``. When ``group_by`` is False
            (default) the output is a list with one item per field and ``output`` has the following effect
            on the items:

            - "auto" (default):
                - when ``keys`` is a str returns a single value per field
                - when ``keys`` is a list/tuple returns a list/tuple of values per field
            - list or "list": returns a list of values per field.
            - tuple or "tuple": returns a tuple of values per field.
            - dict or "dict": returns a dictionary with keys and their values per field.

            When ``group_by_key`` is True the output is grouped by key and return an object with
            one item per key. The item per key contains the list of values for that key from all the
            fields. When ``output`` is "dict" a dict is returned, otherwise a list.

        group_by_key: bool
            When True the output is grouped by key as described in ``output``.
        flatten_dict: bool
            When True and ``output`` is dict, for each field if any of the values in the returned dict
            is itself a dict, it is flattened to depth 1 by concatenating the keys with a dot. For example, if
            the returned dict is ``{"a": {"x": 1, "y": 2}, "b": 3}``, it becomes ``{"a.x": 1, " a.y": 2, "b": 3}``.
            This option is ignored when ``output`` is not dict.
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
        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "test.grib").to_fieldlist()
        >>> fl.get("parameter.variable")
        ['2t', 'msl']
        >>> fl.get(["parameter.variable", "parameter.units"])
        [('2t', 'K'), ('msl', 'Pa')]
        >>> fl.get(("parameter.variable", "parameter.units"))
        [['2t', 'K'], ['msl', 'Pa']]

        """
        pass

    @abstractmethod
    def metadata(self, *args, **kwargs):
        r"""Return the raw metadata values for each field.

        Parameters
        ----------
        *args: tuple
            Positional arguments defining the metadata keys. Passed to
            :obj:`Field.metadata() <earthkit.data.core.field.Field.metadata>`
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`Field.metadata() <earthkit.data.core.field.Field.metadata>`

        Returns
        -------
        list
            List with one item per :obj:`Field <earthkit.data.core.field.Field>`

        Examples
        --------
        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "test.grib").to_fieldlist()
        >>> fl.metadata("param")
        ['2t', 'msl']
        >>> fl.metadata("param", "units")
        [('2t', 'K'), ('msl', 'Pa')]
        >>> fl.metadata(["param", "units"])
        [['2t', 'K'], ['msl', 'Pa']]

        """
        pass

    def set(self, *args, **kwargs):
        r"""Set the metadata values for each field.

        All the arguments are passed to :py:meth:`earthkit.data.core.field.Field.set` for each field in the fieldlist.

        Parameters
        ----------
        *args: tuple
            Positional arguments defining the metadata keys and values.
        **kwargs: dict, optional
            Keyword arguments defining the metadata keys and values.

        Returns
        -------
        FieldList
            New FieldList with the updated metadata values.

        See Also
        --------
        :py:meth:`earthkit.data.core.field.Field.set`

        """
        pass

    @abstractmethod
    def ls(self, n=None, keys="default", extra_keys=None, collections=None):
        r"""Generate a list like summary using a set of metadata keys.

        Parameters
        ----------
        n: int, None
            The number of fields to be
            listed. None means all the fields, ``n > 0`` means fields from the front, while
            ``n < 0`` means fields from the back of the fieldlist.
        keys: list of str, dict, None
            The metadata keys to extract. If ``keys="default"``, a built-in default set of keys is used.
            To specify a column title for each key in the output use a dict as a mapping from the keys to the
            column titles.
        extra_keys: list of str, dict, None
            List of additional keys on top of ``keys``. To specify a column title for each key in the output
            use a dict as a mapping from the keys to the column titles.
        collections: str, list of str, None
            The collections to extract. Can be a single collection (str) or multiple collections as a list of str.
            A collection is a component of the field (e.g. "time", "parameter", "geography", etc.) as a dictionary.
            It can also be a collection within the raw "metadata" component. For example, when a :obj:`Field` was
            created from a GRIB message, the ecCodes GRIB "namespaces" can be accessed as collections,
            e.g. "metadata.mars" means the ecCodes GRIB "mars" namespace.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row per :py:class:`~earthkit.data.core.field.Field`.

        See Also
        --------
        head
        tail

        """
        pass

    @abstractmethod
    def head(self, n=5, **kwargs):
        r"""Generate a list like summary of the first ``n`` fields.

        Same as calling :obj:`ls` with ``n``.

        Parameters
        ----------
        n: int, None
            The number of fields (``n`` > 0) to be printed from the front.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See :obj:`ls`.

        See Also
        --------
        ls
        tail

        Notes
        -----
        The following calls are equivalent:

        .. code-block:: python

            fl.head()
            fl.head(5)
            fl.head(n=5)
            fl.ls(5)
            fl.ls(n=5)

        """
        pass

    @abstractmethod
    def tail(self, n=5, **kwargs):
        r"""Generate a list like summary of the last ``n`` fields.

        Same as calling :obj:`ls` with ``-n``.

        Parameters
        ----------
        n: int, None
            The number of fields (``n`` > 0)  to be printed from the back.
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

            fl.tail()
            fl.tail(5)
            fl.tail(n=5)
            fl.ls(-5)
            fl.ls(n=-5)

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
    ) -> dict | tuple:
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
            When True and only one metadata key is specified, the unique values are returned as a tuple instead
            of a dict. Default is False.
        remapping: dict, optional
            A dictionary for remapping keys or values during collection. Default is None.
        patch: dict, optional
            A dictionary for patching key values during collection. Default is None.
        cache: bool, optional
            Whether to use an a cache attached to the fieldlist for previously collected unique values.
            Default is True.
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
            Positional arguments specifying the filter conditions as a dict.
            Both single or multiple keys are allowed to use. When multiple filter conditions
            are specified, they are combined with a logical AND operator. Each metadata key in
            the filter conditions can specify the following type of filter values:

            - single value::

                fl.sel({parameter.variable: "t"})

            - list of values::

                fl.sel({parameter.variable: ["u", "v"]})

            - slice of values (defines a closed interval, so treated as inclusive of both the start
            and stop values, unlike normal Python indexing). The following example filters the fields
            with "vertical.level" between 300 and 500 inclusively::

                fl.sel({vertical.level: slice(300, 500)})

            Date and time related keys from the "time" field component are automatically normalised
            for comparison. This is also applied to the following keys from the raw
            metadata: "metadata.base_datetime", "metadata.valid_datetime" and "metadata.step_timedelta".

            For example, when filtering by "time.valid_datetime" the following calls are equivalent:

            >>> fl.sel({ "time.valid_datetime": "2018-08-01T12:00:00"})
            >>> fl.sel({ "time.valid_datetime": "2018080112"})
            >>> fl.sel({ "time.valid_datetime": 2018080112})
            >>> fl.sel({ "time.valid_datetime": datetime(2018, 8, 1, 12, 0) })

            Similarly, when filtering by "time.step" the following calls are equivalent (values are assumed
            to be in hours when the unit is not specified):

            >>> fl.sel({ "time.step": "6h"})
            >>> fl.sel({ "time.step": 6})
            >>> fl.sel({ "time.step": "360m"})
            >>> fl.sel({ "time.step": timedelta(hours=6)})

        remapping: dict
            Define new metadata keys from existing ones to use in ``*args`` and ``**kwargs``.
            E.g. to define a new key "param_level" as the concatenated value of
            the "parameter.variable" and "vertical.level" keys use::

            >>> remapping={"param_level": "{parameter.variable}{vertical.level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the filter conditions.

        Returns
        -------
        MaskFieldlist, FieldList
            Returns a MaskFieldList with the reordered fields. It provides a view to the data in the
            original object, so no data is copied. When called without any arguments it returns the
            original fieldlist.


        Examples
        --------
        How-to examples:

        - :ref:`/how-tos/grib/grib_selection.ipynb`

        More examples:

        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "tuv_pl.grib").to_fieldlist()
        >>> len(fl)
        18

        Selecting by a single key ("parameter.variable") with a single value:

        >>> fl1 = fl.sel({parameter.variable: "t"})
        >>> for f in fl1:
        ...     print(f)
        ...
        Field(t,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        Field(t,700,20180801,1200,0,0)
        Field(t,500,20180801,1200,0,0)
        Field(t,400,20180801,1200,0,0)
        Field(t,300,20180801,1200,0,0)

        Selecting by multiple keys ("parameter.variable", "vertical.level") with a list and slice of values:

        >>> fl1 = fl.sel(
        ...     {parameter.variable: ["u", "v"], vertical.level: slice(400, 700)}
        ... )
        >>> for f in fl1:
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

        >>> fl1 = fl.sel(
        ...     param_level=["t850", "u1000"],
        ...     remapping={"param_level": "{parameter.variable}{vertical.level}"},
        ... )
        >>> for f in fl1:
        ...     print(f)
        ...
        Field(u,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        """
        pass

    @abstractmethod
    def order_by(self, *args, remapping=None, patch=None, **kwargs):
        """Change the order of the fields in a fieldlist.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to perform the ordering on. Each argument can be
            a single key (str) or multiple keys as a list/tuple of str or a dictionary.
            Any metadata keys that :meth:`earthkit.data.core.field.Field.get` accepts can be
            used here. The order of the keys defines the priority of the ordering. When a dictionary is used it
            must specify the ordering direction or the order of the values for each key. The ordering direction
            can be either "ascending" or "descending" (the default is "ascending"). The order of values for
            a key is defined by a list of values for that key, which must include all the available values
            for that key in the fieldlist. See the examples below for more details.
        remapping: dict
            Define new metadata keys from existing ones to use in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "parameter.variable"
            and "vertical.level" keys use::

                remapping={"param_level": "{parameter.variable}{vertical.level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the metadata keys to perform the ordering on. Used in
            the same way as a dictionary in ``*args``.


        Returns
        -------
        MaskFieldList, FieldList
            Returns a MaskFieldList with the reordered fields. It provides a view to the data in the
            original object, so no data is copied. When called without any arguments it returns the
            original fieldlist.

        Examples
        --------
        How-to examples:

        - :ref:`/how-tos/grib/grib_order_by.ipynb`


        Ordering by a single metadata key ("parameter.variable"). The default ordering direction
        is ``ascending``:

        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "test6.grib").to_fieldlist()
        >>> for f in fl.order_by("parameter.variable"):
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

        >>> for f in fl.order_by(["vertical.level", "parameter.variable"]):
        ...     print(f)
        ...
        Field(t,850,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)
        Field(t,1000,20180801,1200,0,0)
        Field(u,1000,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)

        Specifying the ordering direction:

        >>> for f in fl.order_by(
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

        >>> for f in fl.order_by({"parameter.variable": ["u", "t", "v"]}):
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
        >>> for f in fl.order_by({"param_level": ordering}, remapping=remapping):
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
    def to_fieldlist(self, array_namespace=None, device=None, flatten=False, dtype=None):
        r"""Change how the values stored in each field in a fieldlist.

        This method converts the data values in each field to an array with a given ``array_namespace``
        and/or ``device``. The resulting fieldlist is then composed of the converted fields.
        The field values are extracted using the :py:meth:`earthkit.data.core.field.Field.to_array` method
        of each field.

        When a field already stores its values as an array with a matching ``array_namespace`` and ``device``, a
        copy of that array is made and stored in the resulting field. This means that even if called without any
        arguments, the resulting fieldlist will have its own copy of the data values.

        The primary use of this method is to convert the values in GRIB fields loaded from disk to in-memory
        arrays. By default, the values in GRIB fields loaded from disk are not stored as arrays in memory, but
        rather as references to the on-disk data. This allows for efficient access to the data without loading
        it all into memory at once. However, in some cases it may be desirable to convert these values to
        in-memory arrays for faster access or for compatibility with other libraries. This method provides a
        way to do that while preserving the metadata of the fields.

        Parameters
        ----------
        array_namespace: str, array_namespace or None
            The array namespace to be used for the field values in the resulting fieldlist. When it is None,
            the default array namespace used by the underlying data accessor of the field is used. For GRIB
            it is "numpy".
        device: str or None
            The device where the array will be allocated. When it is :obj:`None` the default device is used.
        flatten: bool
            When it is True the values are flattened per field. Otherwise the array will have the
            field's :obj:`shape` per field.
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default type used by the underlying
            data accessor per field is used. For GRIB it is ``float64``.

        Returns
        -------
        :class:`SimpleFieldList`
            New fieldlist formed from the converted fields.

        Examples
        --------
        How-to examples:

        - :ref:`/how-tos/grib/grib_array_namespace.ipynb`

        The following example will convert a fieldlist read from a GRIB file into a
        :class:`SimpleFieldList` storing data values as single precision arrays in each field.

        >>> import numpy as np
        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "tuv_pl.grib").to_fieldlist()
        >>> r = fl.to_fieldlist(array_namespace="numpy", dtype=np.float32)
        >>> r.to_numpy().dtype
        dtype('float32')

        """
        pass

    @abstractmethod
    def to_tensor(self, *args, **kwargs):
        """Convert to a tensor-like structure.

        This method is intended to use internally to support the Xarray engine, which converts fieldlist
        to a tensor-like structure before converting it to an Xarray Dataset or DataArray.
        """
        pass

    @abstractmethod
    def to_cube(self, *args, **kwargs):
        """Convert to a cube-like structure.

        This method is intended to support fieldlist usage in the ``anemoi-datasets`` package. Planned to be
        removed in the future and use :obj:`to_tensor` instead.
        """
        pass

    @abstractmethod
    def batched(self, n):
        """Iterate through the fieldlist in batches of ``n`` fields.

        Parameters
        ----------
        n: int
            Batch size.

        Returns
        -------
        object
            Returns an iterator yielding batches of ``n`` fields. Each batch is a new fieldlist
            containing a view to the data in the original object, so no data is copied. The last
            batch may contain fewer than ``n`` fields.

        """
        pass

    @abstractmethod
    def group_by(self, *keys, sort=True):
        """Iterate through the fieldlist in groups defined by metadata keys.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying the metadata keys to group by.
            Keys can be a single or multiple str, or a list or tuple of str.

        sort: bool, optional
            If ``True`` (default), the fieldlist is sorted by the metadata ``keys`` before grouping.

        Returns
        -------
        object
            Returns an iterator yielding batches of fields grouped by the metadata ``keys``. Each
            batch is a new fieldlist containing a view to the data in the original object, so no data
            is copied. It generates a new group every time the value of the ``keys`` change.

        """
        pass

    @abstractmethod
    def _unary_op(self, oper):
        pass

    @abstractmethod
    def _binary_op(self, oper, y):
        pass
