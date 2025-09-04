# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_timedelta

ZERO_TIMEDELTA = to_timedelta(0)


class GribTimeBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.specs.time import SimpleTime

        d = GribTimeBuilder._build_dict(handle)
        r = SimpleTime.from_dict(d)
        r._set_private_data("handle", handle)
        return r

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        def _datetime(date_key, time_key):
            date = _get(date_key, None)
            if date is not None:
                time = _get(time_key, None)
                if time is not None:
                    return datetime_from_grib(date, time)
            return None

        hdate = _get("hdate")
        if hdate is not None:
            time = _get("dataTime")
            base = datetime_from_grib(hdate, time)
        else:
            base = _datetime("dataDate", "dataTime")

        end = None
        time_span = ZERO_TIMEDELTA

        end = _get("endStep")
        if end is None:
            end = _get("step")

        if end is None:
            end = ZERO_TIMEDELTA
        else:
            end = to_timedelta(end)
            start = _get("startStep")
            if start is not None:
                start = to_timedelta(start)
                time_span = end - start

        indexing = _datetime("indexingDate", "indexingTime")
        reference = _datetime("referenceDate", "referenceTime")

        return dict(
            base_datetime=to_datetime(base),
            step=end,
            time_span=time_span,
            indexing_datetime=indexing,
            reference_datetime=reference,
        )

    @staticmethod
    def get_grib_context(time, context) -> dict:
        pass


# def time_from_handle(handle):
#     def _get(key, default=None):
#         return handle.get(key, default=default)

#     def _datetime(date_key, time_key):
#         date = _get(date_key, None)
#         if date is not None:
#             time = _get(time_key, None)
#             if time is not None:
#                 return datetime_from_grib(date, time)
#         return None

#     hdate = _get("hdate")
#     if hdate is not None:
#         time = _get("dataTime")
#         base = datetime_from_grib(hdate, time)
#     else:
#         base = _datetime("dataDate", "dataTime")

#     v = _get("endStep", None)
#     if v is None:
#         v = _get("step", None)
#     step = to_timedelta(v)

#     end = _get("endStep", None)
#     if end is None:
#         return to_timedelta(0)

#     start = _get("startStep", None)
#     if start is None:
#         start = to_timedelta(0)

#     time_span = to_timedelta(end) - to_timedelta(start)

#     indexing = _datetime("indexingDate", "indexingTime")
#     reference = _datetime("referenceDate", "referenceTime")

#     d = dict(
#         base_datetime=to_datetime(base),
#         step=step,
#         time_span=time_span,
#         indexing_datetime=indexing,
#         reference_datetime=reference,
#     )

#     d.from_dict(d)


# def to_grib(spec):
#     raise NotImplementedError("GRIB encoding not implemented.")
