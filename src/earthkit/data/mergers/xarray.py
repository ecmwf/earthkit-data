# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

import xarray as xr
from xarray.backends.common import BackendEntrypoint

LOG = logging.getLogger(__name__)


# We wrap the sources because the FileSource is a os.PathLike and
# since version 0.20, xarray checks the class and change os.PathLike to
# strings. We don't want that, as we want to keep our objects
class WrappedSource:
    """Opaque wrapper protecting a :class:`Source` from xarray's ``os.PathLike`` handling.

    xarray (since 0.20) converts any ``os.PathLike`` argument to a plain string before it reaches a
    backend's ``open_dataset``. Since :class:`earthkit.data.sources.file.FileSource` is itself
    ``os.PathLike``, wrapping it in a plain object lets :class:`EKDEngine` receive the original source.
    """

    def __init__(self, source):
        """Initialize the WrappedSource.

        Parameters
        ----------
        source : :class:`earthkit.data.sources.Source`
            The source to wrap.
        """
        self.source = source


class EKDEngine(BackendEntrypoint):
    """xarray backend entry point that opens a wrapped earthkit-data source via its ``to_xarray`` method."""

    @classmethod
    def open_dataset(cls, filename_or_obj, *args, **kwargs):
        """Open a :class:`WrappedSource` as an xarray dataset.

        Parameters
        ----------
        filename_or_obj : :class:`WrappedSource`
            The wrapped source to open. Must be a :class:`WrappedSource` instance.
        *args
            Unused.
        **kwargs
            Unused.

        Returns
        -------
        xarray.Dataset
        """
        assert isinstance(filename_or_obj, WrappedSource)
        return filename_or_obj.source.to_xarray()


def infer_open_mfdataset_kwargs(
    sources=None,
    paths=None,
    reader_class=None,
    user_kwargs={},
):
    """Compute the keyword arguments to pass to ``xarray.open_mfdataset``.

    Parameters
    ----------
    sources : list of :class:`earthkit.data.sources.Source`, optional
        The sources being merged. Currently unused (the inference logic below it is disabled).
    paths : list of str, optional
        The file paths being merged. Currently unused.
    reader_class : type, optional
        The common reader class of the sources, if any. Currently unused.
    user_kwargs : dict, optional
        User-supplied keyword arguments; ``user_kwargs["xarray_open_mfdataset_kwargs"]`` is merged into the
        result, taking precedence over any inferred options.

    Returns
    -------
    dict
        The keyword arguments to pass to ``xarray.open_mfdataset``.
    """
    result = {}
    result.update(user_kwargs.get("xarray_open_mfdataset_kwargs", {}))
    if False:
        ds = sources[0].to_xarray()
        # lat_dims = [s.get_lat_dim() for s in sources]

        if ds.dims == ["lat", "lon", "forecast_time"]:
            result["concat_dim"] = "forecast_time"

        result.update(user_kwargs)
    return result


def merge(
    sources=None,
    paths=None,
    reader_class=None,
    **kwargs,
):
    """Merge ``sources`` into a single xarray dataset.

    Prefers, in order: a ``to_xarray_multi_from_sources``/``to_xarray_multi_from_paths`` method on
    ``reader_class`` if available; otherwise ``xarray.open_mfdataset`` on ``paths`` if available; otherwise
    ``xarray.open_mfdataset`` on the sources themselves, wrapped (see :class:`WrappedSource`) and opened
    through the :class:`EKDEngine` backend.

    Parameters
    ----------
    sources : list of :class:`earthkit.data.sources.Source`, optional
        The sources to merge. Must not be empty.
    paths : list of str, optional
        The file paths of ``sources``, if they could be resolved.
    reader_class : type, optional
        The common reader class of ``sources``, if it could be resolved.
    **kwargs
        Additional keyword arguments. ``xarray_open_mfdataset_kwargs`` is used to build the options passed
        to ``xarray.open_mfdataset`` (see :func:`infer_open_mfdataset_kwargs`).

    Returns
    -------
    xarray.Dataset
    """
    assert sources

    options = infer_open_mfdataset_kwargs(
        sources=sources,
        paths=paths,
        reader_class=reader_class,
        user_kwargs=kwargs,
    )

    if reader_class is not None and hasattr(reader_class, "to_xarray_multi_from_sources"):
        return reader_class.to_xarray_multi_from_sources(
            sources,
            **options,
        )

    if paths is not None:
        if reader_class is not None and hasattr(reader_class, "to_xarray_multi_from_paths"):
            return reader_class.to_xarray_multi_from_paths(
                paths,
                **options,
            )

        LOG.debug(f"xr.open_mfdataset with options={options}")
        return xr.open_mfdataset(paths, **options)

    LOG.debug(f"xr.open_mfdataset with options= {options}")
    return xr.open_mfdataset(
        [WrappedSource(s) for s in sources],
        engine=EKDEngine,
        **options,
    )
