# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from . import Reader


def is_probably_text(path, probe_size=4096):
    try:
        with open(path, "rb") as f:
            data = f.read(probe_size)

        # if NUL byte, probably binary
        # and not text
        if 0x0 in data:
            return False

        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


class TextReader(Reader):
    _format = "text"
    _binary = False
    _appendable = True

    def __init__(self, source, path):
        super().__init__(source, path)

    def ignore(self):
        # Used by multi-source
        return True

    def to_data_object(self, **kwargs):
        from earthkit.data.data.text import TextData

        return TextData(self)

    def _encode_default(self, encoder, *args, **kwargs):
        return None


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    if deeper_check:
        if is_probably_text(path):
            return TextReader(source, path)


READER = reader
