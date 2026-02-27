# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
from abc import abstractmethod
from collections import defaultdict

import eccodes
from pdbufr.high_level_bufr.bufr import bufr_code_is_coord

from earthkit.data.core import Base
from earthkit.data.core.index import Index
from earthkit.data.core.index import MaskIndex
from earthkit.data.core.index import MultiIndex
from earthkit.data.utils.args import metadata_argument
from earthkit.data.utils.args import metadata_argument_new
from earthkit.data.utils.message import CodesHandle
from earthkit.data.utils.message import CodesMessagePositionIndex
from earthkit.data.utils.message import CodesReader
from earthkit.data.utils.parts import Part
from earthkit.data.utils.summary import make_bufr_html_tree

from .. import Reader
from .pandas import PandasMixIn

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


class BufrCodesMessagePositionIndex(CodesMessagePositionIndex):
    MAGIC = b"BUFR"

    # This does not belong here, should be in the C library
    def _get_message_positions_part(self, fd, part):
        assert part is not None
        assert len(part) == 2

        offset = part[0]
        end_pos = part[0] + part[1] if part[1] > 0 else -1

        if os.lseek(fd, offset, os.SEEK_SET) != offset:
            return

        while True:
            code = os.read(fd, 4)
            if len(code) < 4:
                break

            if code != self.MAGIC:
                offset = os.lseek(fd, offset + 1, os.SEEK_SET)
                continue

            length = self._get_bytes(fd, 3)
            edition = self._get_bytes(fd, 1)

            if end_pos > 0 and offset + length > end_pos:
                return

            if edition in [3, 4]:
                yield offset, length

            offset = os.lseek(fd, offset + length, os.SEEK_SET)


class BUFRCodesHandle(CodesHandle):
    PRODUCT_ID = eccodes.CODES_PRODUCT_BUFR

    def __init__(self, handle, path, offset):
        super().__init__(handle, path, offset)
        self._unpacked = False

    def unpack(self):
        """Decode data section"""
        if not self._unpacked:
            eccodes.codes_set(self._handle, "unpack", 1)
            self._unpacked = True

    def pack(self):
        """Encode data section"""
        if self._unpacked:
            eccodes.codes_set(self._handle, "pack", 1)
            self._unpacked = False

    def json_dump(self, path):
        self.unpack()
        with open(path, "w") as f:
            eccodes.codes_dump(self._handle, f, "json")
        self.pack()

    def __iter__(self):
        class _KeyIterator:
            def __init__(self, handle):
                self._iterator = eccodes.codes_bufr_keys_iterator_new(handle)

            def __del__(self):
                try:
                    eccodes.codes_bufr_keys_iterator_delete(self._iterator)
                except Exception:
                    pass

            def __iter__(self):
                return self

            def __next__(self):
                while True:
                    if not eccodes.codes_bufr_keys_iterator_next(self._iterator):
                        raise StopIteration

                    return eccodes.codes_bufr_keys_iterator_get_name(self._iterator)

        return _KeyIterator(self._handle)

    def keys(self, namespace=None):
        """Iterate over all the available keys"""
        return self.__iter__()

    def as_namespace(self, namespace=None):
        return {k: self.get(k, default=None) for k in self.keys(namespace=namespace)}


class BUFRCodesReader(CodesReader):
    PRODUCT_ID = eccodes.CODES_PRODUCT_BUFR
    HANDLE_TYPE = BUFRCodesHandle


class BUFRMessage(Base):
    r"""Represents a BUFR message in a BUFR file.

    Parameters
    ----------
    path: str
        Path to the BUFR file
    offset: number
        File offset of the message (in bytes)
    length: number
        Size of the message (in bytes)
    """

    def __init__(self, path, offset, length):
        self.path = path
        self._offset = offset
        self._length = length
        self._handle = None

    @property
    def handle(self):
        r""":class:`CodesHandle`: Gets an object providing access to the low level BUFR message structure."""
        if self._handle is None:
            assert self._offset is not None
            self._handle = BUFRCodesReader.from_cache(self.path).at_offset(self._offset)
        return self._handle

    def __repr__(self):
        return "BUFRMessage(type=%s,subType=%s,subsets=%s,%s,%s)" % (
            self.handle.get("dataCategory", default=None),
            self.handle.get("dataSubCategory", default=None),
            self.handle.get("numberOfSubsets", default=None),
            self.handle.get("typicalDate", default=None),
            self.handle.get("typicalTime", default=None),
        )

    def _header(self, key):
        return self.handle.get(key, default=None)

    def subset_count(self):
        """Returns the number of subsets in the given BUFR message."""
        return self._header("numberOfSubsets")

    def is_compressed(self):
        """Checks if the BUFR message contains compressed subsets."""
        return self.subset_count() > 1 and self._header("compressedData") == 1

    def is_uncompressed(self):
        """Checks if the BUFR message contains uncompressed subsets."""
        return self.subset_count() > 1 and self._header("compressedData") == 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handle = None

    def __setitem__(self, key, value):
        """Sets value associated with ``key``"""
        if isinstance(value, list):
            return eccodes.codes_set_array(self.handle._handle, key, value)
        else:
            return eccodes.codes_set(self.handle._handle, key, value)

    def __getitem__(self, key):
        """Returns the value of the ``key``."""
        return self.handle.get(key)

    def __iter__(self):
        """Returns an iterator for the keys the message contains."""
        return self.handle.__iter__()

    def unpack(self):
        """Decodes the data section of the message. When a message is unpacked all
        the keys in the data section become available via :obj:`metadata`.

        See Also
        --------
        :obj:`unpack`
        """
        return self.handle.unpack()

    def pack(self):
        """Encodes the data section of the message. Having called ``pack`` the
        contents of only the header keys become available via :obj:`metadata`. To access
        the data section you need to use :obj:`unpack` again.

        See Also
        --------
        :obj:`unpack`
        """
        return self.handle.unpack()

    def _get_single(self, key, default=None, *, astype=None, raise_on_missing=False):
        try:
            return self.handle.get(key, ktype=astype)
        except Exception:
            pass

        if raise_on_missing:
            raise KeyError(f"Key {key} not found in handle")

        return default

    def _get_fast(
        self,
        keys,
        default=None,
        astype=None,
        raise_on_missing=False,
        output=None,
        flatten_dict=False,
        **kwargs,
    ):
        meth = self._get_single
        result = None

        if isinstance(keys, str):
            result = meth(keys, default=default, astype=astype, raise_on_missing=raise_on_missing)
            if output is dict:
                result = {keys: result}
        elif isinstance(keys, (list, tuple)):
            if output is not dict:
                result = [
                    meth(k, astype=kt, default=d, raise_on_missing=raise_on_missing)
                    for k, kt, d in zip(keys, astype, default)
                ]
            #     if output is tuple:
            #         result = tuple(result)
            else:
                result = {
                    k: meth(k, astype=kt, default=d, raise_on_missing=raise_on_missing)
                    for k, kt, d in zip(keys, astype, default)
                }
        if output is dict and flatten_dict:
            r = {}
            for k, v in result.items():
                if isinstance(v, dict):
                    for _k, _v in v.items():
                        r[k + "." + _k] = _v
                else:
                    r[k] = v
            result = r

        if output is tuple:
            result = tuple(result)

        return result

    def get(
        self,
        keys=None,
        default=None,
        *,
        astype=None,
        raise_on_missing=False,
        output="auto",
        flatten_dict=False,
    ):
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

        keys, astype, default, keys_arg_type = metadata_argument_new(keys, astype=astype, default=default)

        _kwargs = {
            "default": default,
            "raise_on_missing": raise_on_missing,
            # "patches": patches,
            "astype": astype,
        }

        if output == "auto":
            if keys_arg_type is not str:
                output = keys_arg_type
        elif output in [list, "list"]:
            output = list
        elif output in [tuple, "tuple"]:
            output = tuple
        elif output in [dict, "dict"]:
            output = dict
        else:
            raise ValueError(f"Invalid output: {output}")

        return self._get_fast(
            keys,
            default=default,
            astype=astype,
            raise_on_missing=raise_on_missing,
            output=output,
            flatten_dict=flatten_dict,
        )

    def metadata(self, *keys, astype=None, **kwargs):
        r"""Returns metadata values from the BUFR message. When the message in packed
        (default state) only the header keys are available. To access the data section keys
        you need to call :obj:`unpack`.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying metadata keys. Only ecCodes BUFR keys can be used
            here. It can contain a single str or a list or tuple. Can be empty, in this case
            all the keys will
            be used.
        astype: type name, :obj:`list` or :obj:`tuple`
            Return types for ``keys``. A single value is accepted and applied to all the ``keys``.
            Otherwise, must have same the number of elements as ``keys``. Only used when
            ``keys`` is not empty.
        **kwargs: tuple, optional
            Other keyword arguments:

            * default: value, optional
                Specifies the same default value for all the ``keys`` specified. When ``default`` is
                **not present** and a key is not found or its value is a missing value
                :obj:`metadata` will raise KeyError.

        Returns
        -------
        single value, :obj:`list`, :obj:`tuple` or :obj:`dict`
            - when ``keys`` is not empty:
                - single value when ``keys`` is a str
                - otherwise the same type as that of ``keys`` (:obj:`list` or :obj:`tuple`)
            - when ``keys`` is empty:
                - returns a :obj:`dict` with one item per key

        Raises
        ------
        KeyError
            If no ``default`` is set and a key is not found in the message or it has a missing value.

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/temp_10.bufr")
        >>> ds[0].metadata("edition")
        3
        >>> ds[0].metadata("dataCategory", "dataSubCategory")
        (2, 101)

        """
        key, namespace, astype, key_arg_type = metadata_argument(*keys, namespace=None, astype=astype)

        assert isinstance(key, list)
        assert isinstance(namespace, (list, tuple))

        if key:
            assert isinstance(astype, (list, tuple))
            r = [self.handle.get(k, ktype=kt, **kwargs) for k, kt in zip(key, astype)]

            if key_arg_type is str:
                return r[0]
            elif key_arg_type is tuple:
                return tuple(r)
            else:
                return r
        else:
            return self.handle.as_namespace()

    def is_coord(self, key):
        """Check if the specified key is a BUFR coordinate descriptor

        Parameters
        ----------
        key: str
            Key name (can contain ecCodes rank)

        Returns
        -------
        bool
            True if the specified ``key`` is a BUFR coordinate descriptor
        """
        try:
            return bufr_code_is_coord(self.d[key + "->code"])
        except Exception:
            return False

    def dump(self, subset=1):
        r"""Generates a dump with the message content represented as a tree view in a Jupyter notebook.

        Parameters
        ----------
        subset: int
            Subset to dump. Please note that susbset indexing starts at 1. Use None to dump all the
            subsets in the message.

        Returns
        -------
        HTML
            Dump contents represented as a tree view in a Jupyter notebook.

        Examples
        --------
        :ref:`/examples/bufr_temp.ipynb`

        """
        from earthkit.data.core.temporary import temp_file

        with temp_file() as filename:
            self.handle.json_dump(filename)
            with open(filename, "r") as f:
                import json
                import warnings

                try:
                    d = json.loads(f.read())
                    return make_bufr_html_tree(
                        d,
                        self.__repr__(),
                        subset,
                        self.is_compressed(),
                        self.is_uncompressed(),
                    )
                except Exception as e:
                    warnings.warn("Failed to parse bufr_dump", e)
                    return None

    def write(self, f):
        r"""Writes the message to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        """
        self.handle.write_to(f)

    def message(self):
        r"""Returns a buffer containing the encoded message.

        Returns
        -------
        bytes
        """
        return self.handle.get_buffer()


class BUFRListMixIn(PandasMixIn):
    def ls(self, *args, **kwargs):
        r"""Generates a list like summary of the BUFR message list using a set of metadata keys.

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
            DataFrame with one row per :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>`.

        Examples
        --------
        :ref:`/examples/bufr_temp.ipynb`

        """
        from earthkit.data.utils.summary import ls

        def _proc(keys: list, n: int, **kwargs):
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

        return ls(_proc, BUFR_LS_KEYS, *args, **kwargs)

    def head(self, n=5, **kwargs):
        r"""Generates a list like summary of the first ``n``
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
        r"""Generates a list like summary of the last ``n``
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

    def get(self, keys=None, default=None, *, astype=None, raise_on_missing=False, output="item_per_field"):
        r"""Return the values for the specified keys for each message in the list.

        Parameters
        ----------
        keys: str, list or tuple
            Keys to get the values for. Only ecCodes BUFR keys can be used here. It can contain a single
            str or a list or tuple. Can be empty, in this case all the keys will be used.
        default: value
            Default value to return when a key is not found or it has a missing value. When ``default`` is
            **not present** and a key is not found or its value is a missing value :obj:`get` will raise KeyError.
        astype: type name, :obj:`list` or :obj:`tuple`
            Return types for ``keys``. A single value is accepted and applied to all the ``keys``. Otherwise,
            must have same the number of elements as ``keys``. Only used when ``keys`` is not empty.
        raise_on_missing: bool
            When it is True raises an exception if a key is not found in any of the messages in the list or it has a missing value.

        Returns
        -------
        list
            List with one item per :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>`\ s in the list. Each item contains the values for the specified keys for the corresponding message.

        """
        from earthkit.data.utils.args import metadata_argument_new

        # _kwargs = kwargs.copy()
        # astype = _kwargs.pop("astype", None)
        keys, astype, default, keys_arg_type = metadata_argument_new(keys, astype=astype, default=default)

        # assert isinstance(keys, (list, tuple))

        _kwargs = {
            "default": default,
            "raise_on_missing": raise_on_missing,
            # "patches": patches,
            "astype": astype,
        }

        if output == "item_per_field":
            return [f._get_fast(keys, output=keys_arg_type, **_kwargs) for f in self]
        elif output == "item_per_key":
            vals = [f._get_fast(keys, output=keys_arg_type, **_kwargs) for f in self]
            if keys_arg_type in (list, tuple):
                return [[x[i] for x in vals] for i in range(len(keys))]
            else:
                assert isinstance(keys, str)
                return vals
        elif output == "dict_per_field":
            return [f._get_fast(keys, output=dict, **_kwargs) for f in self]
        elif output == "dict_per_key":
            vals = [f._get_fast(keys, output=keys_arg_type, **_kwargs) for f in self]
            if keys_arg_type in (list, tuple):
                result = {k: [] for k in keys}
                for i, k in enumerate(keys):
                    result[k] = [x[i] for x in vals]
            else:
                assert isinstance(keys, str)
                result = {keys: vals}
            return result
        else:
            raise ValueError(
                f"get: invalid output={output}. Must be one of 'item_per_field', 'item_per_key', 'dict_per_field', 'dict_per_key'"
            )

        # result = []
        # for s in self:
        #     result.append(s.get(keys, default=default, astype=astype, raise_on_missing=raise_on_missing))
        # return result

    def metadata(self, *args, **kwargs):
        r"""Returns the metadata values for each message.

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


class BUFRList(PandasMixIn, Index):
    r"""Represent a list of
    :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>`\ s.
    """

    def __init__(self, *args, **kwargs):
        Index.__init__(self, *args, **kwargs)

    # @classmethod
    # def new_mask_index(self, *args, **kwargs):
    #     return MaskBUFRList(*args, **kwargs)

    # @classmethod
    # def merge(cls, sources):
    #     assert all(isinstance(_, BUFRList) for _ in sources)
    #     return MultiBUFRList(sources)

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

        patches: dict, optional
            A dictionary of patches to be applied to the returned values.


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

    # def get(self, keys=None, default=None, *, astype=None, raise_on_missing=False, output="item_per_field"):
    #     r"""Return the values for the specified keys for each message in the list.

    #     Parameters
    #     ----------
    #     keys: str, list or tuple
    #         Keys to get the values for. Only ecCodes BUFR keys can be used here. It can contain a single
    #         str or a list or tuple. Can be empty, in this case all the keys will be used.
    #     default: value
    #         Default value to return when a key is not found or it has a missing value. When ``default`` is
    #         **not present** and a key is not found or its value is a missing value :obj:`get` will raise KeyError.
    #     astype: type name, :obj:`list` or :obj:`tuple`
    #         Return types for ``keys``. A single value is accepted and applied to all the ``keys``. Otherwise,
    #         must have same the number of elements as ``keys``. Only used when ``keys`` is not empty.
    #     raise_on_missing: bool
    #         When it is True raises an exception if a key is not found in any of the messages in the list or it has a missing value.

    #     Returns
    #     -------
    #     list
    #         List with one item per :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>`\ s in the list. Each item contains the values for the specified keys for the corresponding message.

    #     """
    #     from earthkit.data.utils.args import metadata_argument_new

    #     # _kwargs = kwargs.copy()
    #     # astype = _kwargs.pop("astype", None)
    #     keys, astype, default, keys_arg_type = metadata_argument_new(keys, astype=astype, default=default)

    #     # assert isinstance(keys, (list, tuple))

    #     _kwargs = {
    #         "default": default,
    #         "raise_on_missing": raise_on_missing,
    #         # "patches": patches,
    #         "astype": astype,
    #     }

    #     if output == "item_per_field":
    #         return [f._get_fast(keys, output=keys_arg_type, **_kwargs) for f in self]
    #     elif output == "item_per_key":
    #         vals = [f._get_fast(keys, output=keys_arg_type, **_kwargs) for f in self]
    #         if keys_arg_type in (list, tuple):
    #             return [[x[i] for x in vals] for i in range(len(keys))]
    #         else:
    #             assert isinstance(keys, str)
    #             return vals
    #     elif output == "dict_per_field":
    #         return [f._get_fast(keys, output=dict, **_kwargs) for f in self]
    #     elif output == "dict_per_key":
    #         vals = [f._get_fast(keys, output=keys_arg_type, **_kwargs) for f in self]
    #         if keys_arg_type in (list, tuple):
    #             result = {k: [] for k in keys}
    #             for i, k in enumerate(keys):
    #                 result[k] = [x[i] for x in vals]
    #         else:
    #             assert isinstance(keys, str)
    #             result = {keys: vals}
    #         return result
    #     else:
    #         raise ValueError(
    #             f"get: invalid output={output}. Must be one of 'item_per_field', 'item_per_key', 'dict_per_field', 'dict_per_key'"
    #         )

    def metadata(self, *args, **kwargs):
        r"""Returns the metadata values for each message.

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
        r"""Generates a list like summary of the BUFR message list using a set of metadata keys.

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
        :ref:`/examples/bufr_temp.ipynb`

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
        r"""Generates a list like summary of the first ``n``
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
        r"""Generates a list like summary of the last ``n``
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

    def sel(self, *args, **kwargs):
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
        return super().sel(*args, remapping=None, **kwargs)

    def isel(self, *args, **kwargs):
        raise NotImplementedError()

    def order_by(self, *args, **kwargs):
        """Changes the order of the messages in a BUFRList object.

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

    def normalise_key_values(self, **kwargs):
        return kwargs

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        return MaskBUFRList(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, BUFRList) for _ in sources)
        return MultiBUFRList(sources)


class MaskBUFRList(BUFRList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class MultiBUFRList(BUFRList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)


class BUFRInFiles(BUFRList):
    def _getitem(self, n):
        if isinstance(n, int):
            part = self.part(n if n >= 0 else len(self) + n)
            return BUFRMessage(part.path, part.offset, part.length)

    def __len__(self):
        return self.number_of_parts()

    @abstractmethod
    def part(self, n):
        self._not_implemented()

    @abstractmethod
    def number_of_parts(self):
        self._not_implemented()


class BUFRInOneFile(BUFRInFiles):
    def __init__(self, path, parts=None):
        self.path = path
        self._file_parts = parts
        self.__positions = None

    @property
    def _positions(self):
        if self.__positions is None:
            self.__positions = BufrCodesMessagePositionIndex(self.path, parts=self._file_parts)
        return self.__positions

    def part(self, n):
        return Part(self.path, self._positions.offsets[n], self._positions.lengths[n])

    def number_of_parts(self):
        return len(self._positions)


class BUFRReader(BUFRInOneFile, Reader):
    """Represents a BUFR file"""

    appendable = True  # BUFR messages can be added to the same file

    def __init__(self, source, path, parts=None):
        Reader.__init__(self, source, path)
        BUFRInOneFile.__init__(self, path, parts=parts)

    def __repr__(self):
        return "BUFRReader(%s)" % (self.path,)

    @classmethod
    def merge(cls, readers):
        assert all(isinstance(s, BUFRReader) for s in readers), readers
        assert len(readers) > 1

        return MultiBUFRList(readers)

    def mutate_source(self):
        # A BUFRReader is a source itself
        return self

    def default_encoder(self):
        return Reader.default_encoder(self)
