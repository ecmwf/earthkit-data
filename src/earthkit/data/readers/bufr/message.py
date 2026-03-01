# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core import Base
from earthkit.data.core.order import build_remapping
from earthkit.data.utils.args import metadata_argument_new
from earthkit.data.utils.summary import make_bufr_html_tree

from .handle import BUFRCodesReader


class BUFRMessage(Base):
    r"""Represent a BUFR message in a BUFR file.

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
        self.__handle = None

    # TODO: make usage of _handle thread safe
    @property
    def _handle(self):
        r""":class:`CodesHandle`: Gets an object providing access to the low level BUFR message structure."""
        if self.__handle is None:
            assert self._offset is not None
            self.__handle = BUFRCodesReader.from_cache(self.path).at_offset(self._offset)
        return self.__handle

    def __repr__(self):
        return "BUFRMessage(type=%s,subType=%s,subsets=%s,%s,%s)" % (
            self._handle.get("dataCategory", default=None),
            self._handle.get("dataSubCategory", default=None),
            self._handle.get("numberOfSubsets", default=None),
            self._handle.get("typicalDate", default=None),
            self._handle.get("typicalTime", default=None),
        )

    def _header(self, key):
        return self._handle.get(key, default=None)

    def subset_count(self):
        """Return the number of subsets in the given BUFR message."""
        return self._header("numberOfSubsets")

    def is_compressed(self):
        """Check if the BUFR message contains compressed subsets."""
        return self.subset_count() > 1 and self._header("compressedData") == 1

    def is_uncompressed(self):
        """Check if the BUFR message contains uncompressed subsets."""
        return self.subset_count() > 1 and self._header("compressedData") == 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__handle = None

    def __setitem__(self, key, value):
        """Set value associated with key in the underlying ecCodes handle.

        Parameters
        ----------
        key: str
            Key name (can contain ecCodes rank)

        This method violates the immutability of the message, but it is required for pdbufr to work. It is
        not intended to be used by the users of the library.
        """
        return self._handle._set(key, value)

    def __getitem__(self, key):
        """Return the value of the ``key``."""
        return self._handle.get(key)

    def __iter__(self):
        """Return an iterator for the keys the message contains."""
        return self._handle.__iter__()

    def unpack(self):
        """Decode the data section of the message. When a message is unpacked all
        the keys in the data section become available via :obj:`metadata`.

        See Also
        --------
        :obj:`unpack`
        """
        return self._handle.unpack()

    def pack(self):
        """Encode the data section of the message. Having called ``pack`` the
        contents of only the header keys become available via :obj:`metadata`. To access
        the data section you need to use :obj:`unpack` again.

        See Also
        --------
        :obj:`unpack`
        """
        return self._handle.pack()

    def _get_single(self, key, default=None, *, astype=None, raise_on_missing=False):
        try:
            return self._handle.get(key, ktype=astype)
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
        remapping=None,
    ):
        meth = self._get_single
        # Remapping must be an object if defined
        if remapping is not None:
            meth = remapping(meth)

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
        remapping=None,
        patch=None,
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

        if remapping or patch:
            remapping = build_remapping(remapping, patch, forced_build=False)

        return self._get_fast(
            keys,
            default=default,
            astype=astype,
            raise_on_missing=raise_on_missing,
            output=output,
            flatten_dict=flatten_dict,
        )

    def metadata(
        self,
        keys,
        *,
        astype=None,
        output="auto",
        remapping=None,
        patch=None,
    ):
        return self.get(
            keys,
            astype=astype,
            raise_on_missing=True,
            output=output,
            remapping=remapping,
            patch=patch,
        )

    def is_coord(self, key):
        """Check if the specified key is a BUFR coordinate descriptor.

        Parameters
        ----------
        key: str
            Key name (can contain ecCodes rank)

        Returns
        -------
        bool
            True if the specified ``key`` is a BUFR coordinate descriptor
        """

        def _bufr_code_is_coord(code) -> bool:
            if isinstance(code, int):
                return code <= 9999
            else:
                return int(code[:3]) < 10

        try:
            c = self._handle.get(key + "->code", ktype=int)
            return _bufr_code_is_coord(c)
        except Exception:
            return False

    def describe(self, subset=1):
        r"""Generate a dump with the message content represented as a tree view in a Jupyter notebook.

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
            self._handle.json_dump(filename)
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

    def message(self):
        r"""Return a buffer containing the encoded message.

        Returns
        -------
        bytes
        """
        return self.handle.get_buffer()
