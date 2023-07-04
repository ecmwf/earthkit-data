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


class PandasMixIn:
    def to_pandas(self, columns=COLUMNS, filters=None, **kwargs):
        """Extracts BUFR data into a pandas DataFrame using :xref:`pdbufr`.

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
        - :ref:`/examples/bufr_temp.ipynb`
        - :ref:`/examples/bufr_synop.ipynb`

        """
        import pdbufr

        filters = {} if filters is None else filters

        return pdbufr.read_bufr(self, columns=columns, filters=filters, **kwargs)
