from typing import (
    TYPE_CHECKING,
    Any,  # noqa: F401
)

from .source import SourceData

if TYPE_CHECKING:
    import geopandas
    import pandas  # type: ignore[import]


class SQLData(SourceData):
    """Represent SQL data.

    SQL data can be converted with the following methods:

    - :py:func:`to_xarray`
    - :py:func:`to_pandas`
    - :py:func:`to_geopandas`

    """

    _TYPE_NAME = "SQL"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._PANDAS, self._GEOPANDAS]

    def describe(self) -> Any:
        """Provide a description of the GeoTIFF data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the GeoTIFF data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="SQL file", path=self.path, types=self.available_types)

    @property
    def path(self) -> str | list[str] | None:
        try:
            return self._reader.path
        except Exception:
            return None

    def __repr__(self) -> str:
        return f"SQLData(path={self.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_pandas(self, *args, **kwargs) -> "pandas.DataFrame":
        """Convert into a Pandas DataFrame.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the SQL data.
        """
        return self._reader.to_pandas(**kwargs)

    def to_geopandas(self, *args, **kwargs) -> "geopandas.DataFrame":
        """Convert into a Pandas DataFrame.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the SQL data.
        """
        return self._reader.to_geopandas(**kwargs)
