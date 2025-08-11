# (C) Copyright 2021 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
import datetime
import re

from dateutil.parser import isoparse
from dateutil.parser import parse

from earthkit.data.wrappers import Wrapper

VALID_DATE = re.compile(r"\d\d\d\d-?\d\d-?\d\d([T\s]\d\d:\d\d(:\d\d)?)?Z?")


def parse_date(dt):
    if not VALID_DATE.match(dt):
        raise ValueError(f"Invalid datetime '{dt}'")

    try:
        return datetime.datetime.fromisoformat(dt)
    except Exception:
        pass

    try:
        return isoparse(dt)
    except ValueError:
        pass

    return parse(dt)


class StrWrapper(Wrapper):
    def __init__(self, data):
        self.data = data

    def bounding_box(self):
        if "/" in self.data:
            return tuple(float(x) for x in self.data.split("/"))
        else:
            raise ValueError(f"Invalid bounding box '{self.data}'")

    def datetime(self):
        return parse_date(self.data)

    def to_datetime(self):
        return self.datetime()

    def to_datetime_list(self):
        from earthkit.data.utils.dates import mars_like_date_list

        # MARS style lists
        bits = self.data.split("/")
        if len(bits) == 3 and bits[1].lower() == "to":
            return mars_like_date_list(parse_date(bits[0]), parse_date(bits[2]), 1)

        if len(bits) == 5 and bits[1].lower() == "to" and bits[3].lower() == "by":
            return mars_like_date_list(parse_date(bits[0]), parse_date(bits[2]), int(bits[4]))

        return [parse_date(d) for d in bits]

    def to_string(self):
        return self.data


def wrapper(data, *args, fieldlist=False, **kwargs):
    if isinstance(data, str):
        return StrWrapper(data)
    return None
