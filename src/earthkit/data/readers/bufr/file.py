# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import defaultdict

from earthkit.data.core.index import MaskIndex
from earthkit.data.core.index import MultiIndex
from earthkit.data.featurelist.indexed import IndexFeatureListBase
from earthkit.data.sources import Source
from earthkit.data.utils.parts import Part

from .. import Reader
from .core import BUFRReaderBase
from .message import BUFRMessage
from .scan import BufrCodesMessagePositionIndex

COLUMNS = ("latitude", "longitude", "data_datetime")

BUFR_LS_KEYS = {
    "edition": "edition",
    "dataCategory": "type",
    "dataSubCategory": "subtype",
    "bufrHeaderCentre": "c",
    "masterTablesVersionNumber": "mv",
    "localTablesVersionNumber": "lv",
    "numberOfSubsets": "subsets",
    "compressedData": "compr",
    "typicalDate": "typicalDate",
    "typicalTime": "typicalTime",
    "ident": "ident",
    "localLatitude": "lat",
    "localLongitude": "lon",
}


class BUFRList(IndexFeatureListBase):
    r"""Represent a list of
    :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>`\ s.
    """

    def __init__(self, *args, **kwargs):
        IndexFeatureListBase.__init__(self, *args, **kwargs)

    def get(
        self,
        keys,
        default=None,
        astype=None,
        raise_on_missing=False,
        output="auto",
        group_by_key=False,
        flatten_dict=False,
    ):
        r"""Return values for the specified keys from all the messages.

        Parameters
        ----------
        keys: str, list, tuple
            Specify the metadata keys to extract. Can be a single key (str) or multiple
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

        from earthkit.data.utils.args import metadata_argument_new

        keys, astype, default, keys_arg_type = metadata_argument_new(keys, astype=astype, default=default)

        if output == "auto":
            if keys_arg_type is not None:
                output = keys_arg_type
        elif output in [list, "list"]:
            output = list
        elif output in [tuple, "tuple"]:
            output = tuple
        elif output in [dict, "dict"]:
            output = dict
        else:
            raise ValueError(f"Invalid output: {output}")

        _kwargs = {
            "default": default,
            "raise_on_missing": raise_on_missing,
            "flatten_dict": flatten_dict,
            "astype": astype,
        }

        if not group_by_key or output == "auto":
            return [f._get_fast(keys, output=output, **_kwargs) for f in self]
        else:
            if output is dict:
                result = defaultdict(list)
                for f in self:
                    r = f._get_fast(keys, output=dict, **_kwargs)
                    for k, v in r.items():
                        result[k].append(v)
                return dict(result)
            else:
                vals = [f._get_fast(keys, output=list, **_kwargs) for f in self]
                return [[x[i] for x in vals] for i in range(len(keys))]

        return None

    def metadata(self, *args, **kwargs):
        r"""Return the metadata values for each message.

        Parameters
        ----------
        *args: tuple
            Positional arguments defining the metadata keys. Passed to
            :obj:`BUFRMessage.metadata() <data.readers.bufr.bufr.BUFRMessage.metadata>`
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`BUFRMessage.metadata() <data.readers.bufr.bufr.BUFRMessage.metadata>`

        Returns
        -------
        list
            List with one item per :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage.metadata>`

        """
        result = []
        for s in self:
            result.append(s.metadata(*args, **kwargs))
        return result

    def ls(self, n=None, keys="default", extra_keys=None):
        r"""Generate a list like summary of the BUFR message list using a set of metadata keys.

        Parameters
        ----------
        n: int, None
            The number of :obj:`BUFRMEssage <data.readers.bufr.bufr.BUFRMessage>`\ s to be
            listed. ``None`` means all the messages, ``n > 0`` means messages from the front, while
            ``n < 0`` means messages from the back of the list.
        keys: list of str, dict, None
            Metadata keys. To specify a column title for each key in the output use a dict with keys as
            the metadata keys and values as the column titles. If ``keys`` is None the following dict
            will be used to define the titles and the keys::

                {
                    "edition": "edition",
                    "type": "dataCategory",
                    "subtype": "dataSubCategory",
                    "c": "bufrHeaderCentre",
                    "mv": "masterTablesVersionNumber",
                    "lv": "localTablesVersionNumber",
                    "subsets": "numberOfSubsets",
                    "compr": "compressedData",
                    "typicalDate": "typicalDate",
                    "typicalTime": "typicalTime",
                    "ident": "ident",
                    "lat": "localLatitude",
                    "lon": "localLongitude",
                }

        extra_keys: list of str, dict, None
            List of additional keys to ``keys``. To specify a column title for each key in the output
            use a dict.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row per :obj:`BUFRMEssage <data.readers.bufr.bufr.BUFRMessage>`.

        Examples
        --------
        :ref:`/examples/bufr/bufr_temp.ipynb`

        """
        from earthkit.data.utils.summary import ls as summary_ls

        def _proc(n: int, keys: str | list | tuple = None, **kwargs):
            count_start = 0
            if n is None:
                count_end = len(self)
            elif n > 0:
                count_end = n
            else:
                num = len(self)
                count_start = max(0, num + n)
                count_end = num

            for count, msg in enumerate(self):
                if count_start <= count < count_end:
                    yield ({k: msg._header(k) for k in keys})
                elif count >= count_end:
                    break

        if keys == "default":
            keys = BUFR_LS_KEYS

        return summary_ls(_proc, n=n, keys=keys, extra_keys=extra_keys)

    def head(self, n=5, **kwargs):
        r"""Generate a list like summary of the first ``n``
        :obj:`BUFRMEssage <data.readers.bufr.bufr.BUFRMessage>`\ s using a set of metadata keys.
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
        if n <= 0:
            raise ValueError("head: n must be > 0")
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        r"""Generate a list like summary of the last ``n``
        :obj:`BUFRMEssage <data.readers.bufr.bufr.BUFRMessage>`\ s using a set of metadata keys.
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
        if n <= 0:
            raise ValueError("n must be > 0")
        return self.ls(n=-n, **kwargs)

    def sel(self, *args, remapping=None, **kwargs):
        """Use header metadata values to select only certain messages from a BUFRList object.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the filter condition as dict.
            (See below for details).
        **kwargs: dict, optional
            Other keyword arguments specifying the filter conditions.
            (See below for details).

        Returns
        -------
        object
            Returns a new object with the filtered elements. It contains a view to the data in the
            original object, so no data is copied.

        Notes
        -----
        Filter conditions are specified by a set of **metadata** keys either by a dictionary (in
        ``*args``) or a set of ``**kwargs``. Both single or multiple keys are allowed to use and each
        can specify the following type of filter values:

        - single value::

            ds.sel(dataCategory="2")

        - list of values::

            ds.sel(dataCategory=[1, 2])

        - **slice** of values (defines a **closed interval**, so treated as inclusive of both the start
        and stop values, unlike normal Python indexing)::

            # filter dataCategory between 1 and 4 inclusively
            ds.sel(dataCategory=slice(1,4))
        """
        kwargs.pop("remapping", None)
        return super().sel(*args, remapping=remapping, **kwargs)

    def isel(self, *args, **kwargs):
        raise NotImplementedError()

    def order_by(self, *args, **kwargs):
        """Change the order of the messages in a BUFRList object.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to perform the ordering on.
            (See below for details)
        **kwargs: dict, optional
            Other keyword arguments specifying the metadata keys to perform the ordering on.
            (See below for details)

        Returns
        -------
        object
            Returns a new object with reordered messages. It contains a view to the data in the
            original object, so no data is copied.

        """
        kwargs.pop("remapping", None)
        return super().order_by(*args, remapping=None, **kwargs)

    def _normalise_key_values(self, **kwargs):
        return kwargs

    def to_pandas(self, columns=None, filters=None, **kwargs):
        """Extract BUFR data into a pandas DataFrame using :xref:`pdbufr`.

        Parameters
        ----------
        columns: str, sequence[str]
            List of ecCodes BUFR keys to extract for each BUFR message/subset.
            See: :xref:`read_bufr` for details.
        filters: dict
            Defines the conditions when to extract the specified ``columns``. See:
            :xref:`read_bufr` for details.
        **kwargs: dict, optional
            Other keyword arguments passed to :xref:`read_bufr`.

        Returns
        -------
        Pandas DataFrame

        Examples
        --------
        - :ref:`/examples/bufr/bufr_temp.ipynb`
        - :ref:`/examples/bufr/bufr_synop.ipynb`

        """
        import pdbufr

        columns = [] if columns is None else columns
        filters = {} if filters is None else filters

        return pdbufr.read_bufr(self, columns=columns, filters=filters, **kwargs)

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        return MaskBUFRList(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, BUFRList) for _ in sources)
        return MultiBUFRList(sources)

    def to_data_object(self):
        from earthkit.data.data.featurelist import FeatureListData

        return FeatureListData(self)

    def _default_encoder(self):
        return "bufr"

    def _encode(self, encoder, **kwargs):
        return encoder._encode_featurelist(self, **kwargs)


class MaskBUFRList(BUFRList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)

    def describe(self, *args, **kwargs):
        pass

    def to_data_object(self):
        from earthkit.data.data.featurelist import FeatureListData

        return FeatureListData(self)

    def _encode(self, encoder, **kwargs):
        return encoder._encode_featurelist(self, **kwargs)


class MultiBUFRList(BUFRList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)

    def describe(self, *args, **kwargs):
        pass

    def to_data_object(self):
        from earthkit.data.data.featurelist import FeatureListData

        return FeatureListData(self)

    def _encode(self, encoder, **kwargs):
        return encoder._encode_featurelist(self, **kwargs)


class BUFRListInFile(BUFRList, BUFRReaderBase):
    def __init__(self, path, parts=None, positions=None):
        self.path = path
        self._file_parts = parts
        # self._file = BUFRInOneFile(path, parts=parts)
        self.__positions = positions

    @property
    def _positions(self):
        if self.__positions is None:
            self.__positions = BufrCodesMessagePositionIndex(self.path, parts=self._file_parts)
        return self.__positions

    def _getitem(self, n):
        if isinstance(n, int):
            part = self.part(n if n >= 0 else len(self) + n)
            return BUFRMessage(part.path, part.offset, part.length)

    def __len__(self):
        return self.number_of_parts()

    def part(self, n):
        pos = self._positions
        return Part(self.path, pos.offsets[n], pos.lengths[n])

    def number_of_parts(self):
        return len(self._positions)

    def to_data_object(self):
        from earthkit.data.data.bufr import BUFRData

        return BUFRData(self)

    def describe(self, *args, **kwargs):
        pass


class BUFRReader(Source, BUFRReaderBase):
    def __init__(self, source, path, parts=None, positions=None):
        self._ori_source = source
        self._kwargs = {"parts": parts, "positions": positions}

        Reader.__init__(self, source, path)

    def to_featurelist(self, *args, **kwargs):
        return BUFRListInFile(self.path, **self._kwargs, **kwargs)

    def to_pandas(self, *args, **kwargs):
        return self.to_featurelist().to_pandas(*args, **kwargs)

    def mutate_source(self):
        # A BUFRReader is a source itself
        return self

    def is_streamable_file(self):
        return False

    def to_data_object(self):
        from earthkit.data.data.bufr import BUFRData

        return BUFRData(self)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(s, BUFRReader) for s in sources)
        return MultiBUFRReader(sources)

    def _encode_default(self, encoder, *args, **kwargs):
        return encoder._encode_featurelist(self.to_featurelist(), *args, **kwargs)


class MultiBUFRReader(Source, BUFRReaderBase):
    def __init__(self, sources):
        self.sources = list(self._flatten(sources))

    def _flatten(self, sources):
        for s in sources:
            if isinstance(s, MultiBUFRReader):
                yield from self._flatten(s.sources)
            else:
                yield s

    def to_featurelist(self):
        fs = [s.to_featurelist() for s in self.sources]
        from earthkit.data.mergers import merge_by_class

        merged = merge_by_class(fs)
        if merged is not None:
            return merged.mutate()

        raise NotImplementedError("Conversion of MultiBUFRReader to featurelist is not implemented")

    def to_pandas(self, *args, **kwargs):
        return self.to_featurelist().to_pandas(*args, **kwargs)

    def __repr__(self):
        return f"MultiBUFRReader({self.sources})"

    def to_data_object(self):
        from earthkit.data.data.bufr import BUFRData

        return BUFRData(self)

    @classmethod
    def merge(cls, sources):
        r = []
        for source in sources:
            if isinstance(source, MultiBUFRReader):
                r.extend(source.sources)
            elif isinstance(source, BUFRReader):
                r.append(source)
            elif not source.ignore():
                raise ValueError(f"Cannot merge source of type {type(source)} in MultiBUFRReader.merge")

        if r:
            return MultiBUFRReader(r)

        raise ValueError("No BUFRReader found in sources to merge")

    def _encode(self, encoder, hints=None, **kwargs):
        return self.to_featurelist()._encode(encoder, hints, **kwargs)

    def _encode_default(self, encoder, hints=None, **kwargs):
        return self.to_featurelist()._encode(encoder, hints, **kwargs)
