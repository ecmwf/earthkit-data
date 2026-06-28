from . import EncodedData, Encoder, FilePathEncodedData


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
    """Encode BUFR data."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        target=None,
        **kwargs,
    ):
        return data._encode(self, target=target)

    def _encode_message(self, message, *, target=None, **kwargs):
        handle = message._handle
        return BufrEncodedData(handle)

    def _encode(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_featurelist(self, fl, *, target=None, **kwargs):
        for f in fl:
            yield f._encode(self, target=target, **kwargs)

        # if path is not None and target is not None and target._name == "file":
        #     # Write file as is if target is file and path is provided.
        #     # Otherwise encode in memory and write to target
        #     return FilePathEncodedData(path, binary)
        # else:
        #     # Encode the data message by message
        #     def _gen(fs, **kwargs):
        #         for f in fs:
        #             yield f._encode(self, **kwargs)

        #     return _gen(fs, **kwargs)

    def _encode_field(self, *args, **kwargs):
        raise NotImplementedError

    def _encode_fieldlist(self, *args, **kwargs):
        raise NotImplementedError

    def _encode_xarray(self, data, **kwargs):
        raise NotImplementedError

    def _encode_path(self, *, path_info=None, target=None, **kwargs):
        # Write file as is if target is file and path is provided.
        if (
            path_info is not None
            and path_info.path is not None
            and path_info.default_encoder == "bufr"
            and target is not None
            and target._name == "file"
        ):
            return FilePathEncodedData(path_info.path, binary=path_info.binary)
        else:
            return None


encoder = BufrEncoder
