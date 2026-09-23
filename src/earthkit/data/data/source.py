# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from . import SimpleData


class SourceData(SimpleData):
    def __init__(self, source_or_reader):
        """Initialize a SourceData object with a source or reader.

        Parameters
        ----------
        source_or_reader : Source or Reader
            The source or reader object that provides access to the data.

        Raises
        ------
        TypeError
            If source_or_reader is not a Source or Reader.
        ValueError
            If no valid Reader can be extracted from source_or_reader.
        """
        from earthkit.data.readers import Reader
        from earthkit.data.sources import Source

        self._source = None
        self._reader = None

        if isinstance(source_or_reader, Source):
            self._source = source_or_reader
            if isinstance(source_or_reader, Reader):
                self._reader = source_or_reader
            elif hasattr(source_or_reader, "_reader") and isinstance(source_or_reader._reader, Reader):
                self._reader = source_or_reader._reader
            else:
                self._reader = self._source
        elif isinstance(source_or_reader, Reader):
            self._reader = source_or_reader
            self._source = source_or_reader.source
        else:
            raise TypeError(f"Invalid type={type(source_or_reader)}. Must be a Source or Reader")

        if self._reader is None:
            raise ValueError(f"SourceData no Source or Reader found in {source_or_reader=}")

    def _default_encoder(self):
        """Return the default encoder for this data object.

        Returns
        -------
        Encoder
            The default encoder object.

        Raises
        ------
        NotImplementedError
            If no default encoder is found.
        """
        if hasattr(self._source, "_default_encoder"):
            return self._source._default_encoder()
        elif hasattr(self._reader, "_default_encoder"):
            return self._reader._default_encoder()
        raise NotImplementedError("No default encoder found for this data object")

    def to_target(self, target, *args, **kwargs):
        """Write the data to a target.

        Parameters
        ----------
        target: str
            The target to write to. See :py:func:`to_target` for more details on the supported targets.
        *args
            Positional arguments to pass to the :func:`to_target`
        **kwargs
            Keyword arguments to pass to the :func:`to_target`. Cannot specify ``data`` in kwargs.

        See Also
        --------
        :py:func:`to_target`
        """
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self._source, **kwargs)

    @property
    def path(self) -> str | list[str] | None:
        try:
            return self._reader.path
        except Exception:
            return None
