# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

LOG = logging.getLogger(__name__)

COLUMNS = ("latitude", "longitude", "data_datetime")

# todo: remove it when pdbufr with message list support is released
_MESSAGE_LIST_SUPPORT = None


def has_message_list_support():
    global _MESSAGE_LIST_SUPPORT
    if _MESSAGE_LIST_SUPPORT is None:
        try:
            from pdbufr.bufr_read import _read_bufr  # noqa

            _MESSAGE_LIST_SUPPORT = True
        except Exception:
            _MESSAGE_LIST_SUPPORT = False

    return _MESSAGE_LIST_SUPPORT


class PandasMixIn:
    def to_pandas(self, columns=COLUMNS, filters=None, **kwargs):
        """Extracts BUFR data into a pandas DataFranme using :xref:`pdbufr`.

        Parameters
        ----------
        columns: str, sequence[str]
            List of ecCodes BUFR keys to extract for each BUFR message/subset.
            See: :xref:`read_bufr` for details.
        filters: dict
            Defines the conditions when to extract the specified ``columns``. See:
            :xref:`read_bufr` for details.
        **kwargs: dict, optional
            Other keyword arguments:

        Returns
        -------
        Pandas DataFrame

        Examples
        --------
        :ref:`/examples/bufr.ipynb`

        """
        import pdbufr

        filters = {} if filters is None else filters

        if has_message_list_support():
            return pdbufr.read_bufr(self, columns=columns, filters=filters, **kwargs)
        else:
            if hasattr(self, "path"):
                return pdbufr.read_bufr(self.path, columns=columns, filters=filters)
            else:
                raise NotImplementedError(
                    "to_pandas is only supported for single files"
                )
