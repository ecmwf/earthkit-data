from . import EncodedData
from . import Encoder
from . import FilePathEncodedData


class BufrEncodedData(EncodedData):
    def __init__(self, handle):
        self.handle = handle

    def to_bytes(self):
        return self.handle.get_buffer()

    def to_file(self, f):
        self.handle.write(f)

    def get(self, key, default=None):
        if key:
            return self.to_field().get(key, default=default)
        else:
            raise NotImplementedError


class BufrEncoder(Encoder):
    """Encode BUFR data"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        target=None,
        **kwargs,
    ):
        return data._encode(self, target=target)

    def _encode_message(self, message):
        handle = message._handle
        return BufrEncodedData(handle)

    def _encode(self, data, **kwargs):
        raise NotImplementedError

    def _encode_featurelist(self, fs, path=None, binary=True, target=None, **kwargs):
        if path is not None and target is not None and target._name == "file":
            # All write file as is if target is file, otherwise encode in memory and write to target
            return FilePathEncodedData(path, binary)
        else:
            # Encode the data message by message
            def _gen(fs, **kwargs):
                for f in fs:
                    yield f._encode(self, **kwargs)

            return _gen(fs, **kwargs)

    def _encode_field(self, *args, **kwargs):
        raise NotImplementedError

    def _encode_fieldlist(self, *args, **kwargs):
        raise NotImplementedError

    def _encode_xarray(self, data, **kwargs):
        raise NotImplementedError


encoder = BufrEncoder
