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

from dateutil.parser import isoparse, parse

from earthkit.data.translators import Translator

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


class StrTranslator(Translator):
    def __init__(self, data):
        self.data = data.to_string(*args, **kwargs)



def translator(data, cls, *args, **kwargs):
    if cls in [str, 'string']:
        return StrTranslator(data, *args, **kwargs)

    return None
