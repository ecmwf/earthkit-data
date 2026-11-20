# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""In-memory model of the CF ``atmosphere_hybrid_sigma_pressure_coordinate``."""

import logging
from collections.abc import Iterable

import numpy as np

from .parametric_vertical import ParametricVerticalCoordinate, get_cf_attribute, register_parametric_vertical

LOG = logging.getLogger(__name__)


def _as_float_array(value, name, ndim, shape=None):
    try:
        arr = np.array(value, dtype=np.float64)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name} must be a numeric array: {e}") from e

    if arr.ndim != ndim:
        raise ValueError(f"{name} must be a {ndim}D array, got shape {arr.shape}")

    if shape is not None and arr.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {arr.shape}")

    arr.setflags(write=False)
    return arr


def _as_levels(levels, name="levels"):
    """Convert ``levels`` to a 1D int64 array, rejecting non-integer values and duplicates."""
    try:
        arr = np.asarray(levels)
        if arr.dtype.kind not in "iu":
            f = arr.astype(np.float64)
            if not np.all(np.isfinite(f)) or not np.all(f == np.round(f)):
                raise ValueError("values must be integers")
            arr = f
        arr = np.array(arr, dtype=np.int64)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name} must be an array of integers: {e}") from e

    if arr.ndim != 1:
        raise ValueError(f"{name} must be a 1D array, got shape {arr.shape}")

    if len(np.unique(arr)) != len(arr):
        raise ValueError(f"{name} must not contain duplicates")

    arr.setflags(write=False)
    return arr


def _as_positive(value, what="positive"):
    """Return ``value`` as "down" or "up" (case-insensitive), raising ValueError for anything else."""
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("down", "up"):
            return v
    raise ValueError(f"{what} must be 'down' or 'up', got {value!r}")


# absolute tolerances of the surface / zero pressure top checks of the completeness rule
_B_TOLERANCE = 1e-9
_AP_TOLERANCE = 1e-6  # Pa


def _is_hybrid_level_type(level_type):
    from earthkit.data.field.component.level_type import LevelTypes

    hybrid = LevelTypes.HYBRID.value
    return level_type is hybrid or level_type == hybrid or level_type == hybrid.name


@register_parametric_vertical
class AtmosphereHybridSigmaPressureCoordinate(ParametricVerticalCoordinate):
    """CF ``atmosphere_hybrid_sigma_pressure_coordinate``.

    The pressure at (full) level ``k`` is ``p(k) = ap(k) + b(k) * ps`` where ``ps`` is the surface
    pressure. The dimensionless coordinate value is ``ap(k) / p0 + b(k)``.

    The model works on the full levels. The optional bounds hold the values on the two half
    levels that enclose each level, ordered in **level order**: ``(half level k-1, half level k)``
    for level ``k``. The level numbers increase in the ``positive`` direction, so for
    ``positive="down"`` (the IFS/GRIB convention) level 1 is at the top and the bounds are ordered
    ``(upper, lower)``, i.e. from the model top towards the surface; for ``positive="up"`` level 1 is
    at the bottom (the surface side) and the bounds are ordered ``(lower, upper)``. For levels
    computed with :meth:`from_half_levels` the bounds are the corresponding half level coefficients
    and the full level values are their mean (IFS convention).

    The level numbers are either known (``levels``) or unknown. Unknown level numbers can be given a
    provisional numbering (e.g. ``1..n`` by ascending coordinate value when decoded from a dataset
    with :meth:`from_xarray`; ``1..n`` in array order for an object created directly with
    ``levels=None``). The provisional numbering is only used to order the levels, it never counts as
    known level numbers.

    **Completeness rule.** The half level coefficients of the whole model are only rebuilt
    (:meth:`can_rebuild_half_levels`, :meth:`to_level_parameters`, :meth:`to_vertical`) when the
    object proves that it holds the whole model: the bounds are available and contiguous in level
    order, the half level at the surface end (given by ``positive``: the last for "down") is the
    surface (``b == 1`` within 1e-9 and ``ap == 0`` within 1e-6 Pa) and either the levels are known
    and are exactly ``1..n`` or (provisional numbering) the half level at the other end is a
    zero-pressure model top (``ap == 0`` and ``b == 0``, same tolerances). A contiguous subset (e.g.
    a prefix or a suffix of the model) is therefore not rebuilt. As the earthkit hybrid level type is
    positive down and the GRIB ``pv`` array is ordered from the top, ``positive="up"`` is never rebuilt.
    :meth:`level_numbers` uses the same evidence for unknown levels.

    Parameters
    ----------
    ap: array-like
        Hybrid ``ap`` coefficient (Pa) on the levels, shape ``(n,)``.
    b: array-like
        Hybrid ``b`` coefficient (dimensionless) on the levels, shape ``(n,)``.
    ap_bnds: array-like, optional
        Bounds of ``ap``, shape ``(n, 2)``. Must be specified together with ``b_bnds``.
    b_bnds: array-like, optional
        Bounds of ``b``, shape ``(n, 2)``. Must be specified together with ``ap_bnds``.
    levels: array-like of int, optional
        Model level numbers (1-based) of the levels, shape ``(n,)``. Duplicates are not allowed.
    p0: float
        Reference pressure (Pa) used to compute the dimensionless coordinate values. 0 means that it
        is unknown (e.g. decoded from the ``a`` form without ``p0``); the dimensionless values then
        require an explicit positive ``p0``.
    ps_name: str or None
        Name of the surface pressure variable. None means it is not known (e.g. a dataset
        without a ``ps`` formula term).
    positive: str
        Direction in which the level numbers increase: "down" (level 1 at the top, the default) or "up"
        (level 1 at the bottom). Case-insensitive.

    Raises
    ------
    ValueError
        If the shapes of the arrays are not consistent, only one of the bounds is specified,
        ``levels`` has duplicates or ``positive`` is invalid.
    """

    STANDARD_NAME = "atmosphere_hybrid_sigma_pressure_coordinate"
    COMPUTED_STANDARD_NAME = "air_pressure"
    TERMS = ("a", "b", "ps", "p0", "ap")

    def __init__(self, ap, b, *, ap_bnds=None, b_bnds=None, levels=None, p0=100000.0, ps_name="ps", positive="down"):
        self._positive = _as_positive(positive)

        self._ap = _as_float_array(ap, "ap", 1)
        n = self._ap.shape[0]
        if n == 0:
            raise ValueError("At least one level is required")
        self._b = _as_float_array(b, "b", 1, (n,))

        if (ap_bnds is None) != (b_bnds is None):
            raise ValueError("ap_bnds and b_bnds must be specified together")

        if ap_bnds is not None:
            self._ap_bnds = _as_float_array(ap_bnds, "ap_bnds", 2, (n, 2))
            self._b_bnds = _as_float_array(b_bnds, "b_bnds", 2, (n, 2))
        else:
            self._ap_bnds = None
            self._b_bnds = None

        if levels is not None:
            self._levels = _as_levels(levels)
            if self._levels.shape != (n,):
                raise ValueError(f"levels must have shape {(n,)}, got {self._levels.shape}")
            self._provisional = None
        else:
            self._levels = None
            # provisional numbering of unknown levels: the array order is the level order unless
            # from_xarray() sets another one. It is kept apart from the known levels on purpose.
            self._provisional = np.arange(1, n + 1, dtype=np.int64)
            self._provisional.setflags(write=False)

        try:
            self._p0 = float(p0)
        except (TypeError, ValueError) as e:
            raise ValueError(f"p0 must be a number, got {p0!r}") from e

        if ps_name is not None and (not isinstance(ps_name, str) or not ps_name):
            raise ValueError(f"ps_name must be None or a non-empty str, got {ps_name!r}")
        self._ps_name = ps_name

    # ------------------------------------------------------------------
    # properties
    # ------------------------------------------------------------------

    @property
    def ap(self):
        """numpy.ndarray: Read-only ``ap`` coefficient (Pa) on the levels, shape ``(n,)``."""
        return self._ap

    @property
    def b(self):
        """numpy.ndarray: Read-only ``b`` coefficient on the levels, shape ``(n,)``."""
        return self._b

    @property
    def ap_bnds(self):
        """numpy.ndarray or None: Read-only bounds of ``ap``, shape ``(n, 2)``."""
        return self._ap_bnds

    @property
    def b_bnds(self):
        """numpy.ndarray or None: Read-only bounds of ``b``, shape ``(n, 2)``."""
        return self._b_bnds

    @property
    def levels(self):
        """numpy.ndarray or None: Read-only known model level numbers (1-based), shape ``(n,)``.

        None when the level numbers are unknown, even if a provisional numbering is used internally
        (see :meth:`level_numbers`).
        """
        return self._levels

    @property
    def positive(self):
        """str: Direction in which the level numbers increase, "down" or "up"."""
        return self._positive

    @property
    def p0(self):
        """float: Reference pressure (Pa)."""
        return self._p0

    @property
    def ps_name(self):
        """Str or None: Name of the surface pressure variable."""
        return self._ps_name

    @property
    def number_of_levels(self):
        """int: Number of levels ``n`` held by the object (not the number of model levels)."""
        return self._ap.shape[0]

    def __len__(self):
        return self._ap.shape[0]

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(n={len(self)}, levels={None if self._levels is None else self._levels.tolist()}"
            f", bounds={self._ap_bnds is not None}, p0={self._p0}, ps_name={self._ps_name!r}"
            f", positive={self._positive!r})"
        )

    # ------------------------------------------------------------------
    # creation
    # ------------------------------------------------------------------

    @classmethod
    def from_half_levels(cls, A, B, levels=None, positive="down", **kwargs):
        """Create the object from the hybrid half level coefficients.

        Parameters
        ----------
        A: array-like
            ``A`` coefficients (Pa) on the ``N+1`` half levels, ordered by level number: from the model
            top to the surface for ``positive="down"``, from the surface to the model top for
            ``positive="up"``.
        B: array-like
            ``B`` coefficients on the ``N+1`` half levels.
        levels: array-like of int, optional
            Model level numbers (1-based, within ``1..N``) to use, in any order. Default: ``1..N``.
            Level ``k`` lies between half levels ``k-1`` and ``k``: ``(upper, lower)`` for "down",
            ``(lower, upper)`` for "up".
        positive: str
            Direction in which the level numbers increase, "down" or "up" (case-insensitive).
        **kwargs
            Passed to the constructor (``p0``, ``ps_name``).

        Returns
        -------
        AtmosphereHybridSigmaPressureCoordinate
            ``ap`` and ``b`` are the means of the two enclosing half level values, the bounds are the
            half level values themselves.

        Raises
        ------
        ValueError
            If ``A`` and ``B`` are not 1D arrays of the same length (at least 2), or ``levels`` has
            duplicates or values out of range, or ``positive`` is invalid.
        """
        positive = _as_positive(positive)
        A = _as_float_array(A, "A", 1)
        B = _as_float_array(B, "B", 1, A.shape)
        if A.shape[0] < 2:
            raise ValueError("A and B must have at least 2 elements")
        N = A.shape[0] - 1

        if levels is None:
            levels = np.arange(1, N + 1, dtype=np.int64)
        else:
            levels = _as_levels(levels)
            if levels.size == 0:
                raise ValueError("levels must not be empty")
            if levels.min() < 1 or levels.max() > N:
                raise ValueError(f"levels must be within 1..{N}, got {levels.tolist()}")

        ap_bnds = np.stack([A[levels - 1], A[levels]], axis=1)
        b_bnds = np.stack([B[levels - 1], B[levels]], axis=1)

        return cls(
            ap_bnds.mean(axis=1),
            b_bnds.mean(axis=1),
            ap_bnds=ap_bnds,
            b_bnds=b_bnds,
            levels=levels,
            positive=positive,
            **kwargs,
        )

    @classmethod
    def from_level_parameters(cls, params, levels=None, positive="down", **kwargs):
        """Create the object from hybrid level parameters.

        Parameters
        ----------
        params: LevelParameters
            Any level parameters object with hybrid level type (e.g. :class:`HybridLevelParameters`).
        levels: array-like of int, optional
            See :meth:`from_half_levels`.
        positive: str
            See :meth:`from_half_levels`.
        **kwargs
            Passed to the constructor.

        Raises
        ------
        ValueError
            If ``params`` is not a hybrid level parameters object.
        """
        level_type = params.level_type() if hasattr(params, "level_type") else None
        if not _is_hybrid_level_type(level_type) or not hasattr(params, "coefficients"):
            raise ValueError(f"Cannot create {cls.__name__} from {params!r}: not hybrid level parameters")

        coeffs = params.coefficients()
        if coeffs is None or len(coeffs) != 2:
            raise ValueError(f"Cannot create {cls.__name__} from {params!r}: A and B coefficients are required")

        A, B = coeffs
        return cls.from_half_levels(A, B, levels=levels, positive=positive, **kwargs)

    @classmethod
    def from_verticals(cls, verticals, **kwargs):
        """Create the object from the vertical components of fields.

        Parameters
        ----------
        verticals: Vertical or iterable of Vertical
            ``Field.vertical`` components. Each must be a hybrid vertical with coefficients (a
            :class:`ParametricVertical`). All of them must have identical ``A`` and ``B`` and the
            same ``positive()`` (None is taken as "down").
        **kwargs
            Passed to the constructor. ``positive`` is taken from the verticals; a ``positive``
            keyword that differs from it is an error.

        Returns
        -------
        AtmosphereHybridSigmaPressureCoordinate
            Same as :meth:`from_half_levels` with the unique levels of ``verticals`` in
            first-seen order and the ``positive`` of the verticals.

        Raises
        ------
        ValueError
            If ``verticals`` is empty, a vertical is not hybrid or has no coefficients, the
            coefficients or the ``positive`` directions differ.
        """
        if hasattr(verticals, "level_type") and hasattr(verticals, "coefficients"):
            verticals = [verticals]
        elif not isinstance(verticals, Iterable):
            raise ValueError(f"Expected a vertical or an iterable of verticals, got {type(verticals)}")

        A = B = None
        positive = None
        levels = {}
        for v in verticals:
            level_type = v.level_type()
            if not _is_hybrid_level_type(level_type):
                raise ValueError(f"Vertical with level type {level_type!r} is not hybrid")

            v_positive = v.positive()
            v_positive = "down" if v_positive is None else _as_positive(v_positive, "The positive of a vertical")
            if positive is None:
                positive = v_positive
            elif positive != v_positive:
                raise ValueError(f"Verticals have different positive directions: {positive!r} and {v_positive!r}")

            coeffs = v.coefficients()
            if coeffs is None:
                raise ValueError("Vertical has no hybrid coefficients")

            vA, vB = (np.asarray(x, dtype=np.float64) for x in coeffs)
            if A is None:
                A, B = vA, vB
            elif not (np.array_equal(A, vA) and np.array_equal(B, vB)):
                raise ValueError("Verticals have different hybrid coefficients")

            level = v.level()
            if level is None:
                raise ValueError("Hybrid vertical has no level")
            levels[level] = None

        if A is None:
            raise ValueError("No verticals specified")

        if "positive" in kwargs and _as_positive(kwargs.pop("positive")) != positive:
            raise ValueError(f"The positive keyword differs from the positive of the verticals ({positive!r})")

        return cls.from_half_levels(A, B, levels=list(levels), positive=positive, **kwargs)

    # ------------------------------------------------------------------
    # conversion to earthkit objects
    # ------------------------------------------------------------------

    def _level_order(self):
        """Return the array indices sorted by level number (known or provisional), or None if unknown."""
        if self._levels is not None:
            return np.argsort(self._levels, kind="stable")
        if self._provisional is not None:
            return np.argsort(self._provisional, kind="stable")
        return None

    def _half_level_chain(self):
        """Return the half level ``(A, B)`` in level order from the bounds, or raise ValueError.

        The bounds must be available and contiguous in level order. Neither the surface nor the
        completeness of the model is checked here.
        """
        if self._ap_bnds is None:
            raise ValueError("Cannot rebuild half level coefficients: no bounds available")

        order = self._level_order()
        if order is None:
            raise ValueError("Cannot rebuild half level coefficients: the order of the levels is unknown")

        result = []
        for name, bnds in (("ap", self._ap_bnds), ("b", self._b_bnds)):
            bnds = bnds[order]
            # exact for coefficients that come from the same half levels, tolerance only absorbs rounding
            if not np.allclose(bnds[:-1, 1], bnds[1:, 0], rtol=1e-12, atol=0.0):
                raise ValueError(f"Cannot rebuild half level coefficients: {name} bounds are not contiguous")
            result.append(np.concatenate([bnds[:, 0], bnds[-1:, 1]]))

        return result[0], result[1]

    def _check_ends(self, A, B, top):
        """Check that the half level at the surface end is the surface and, if ``top``, the other end is a zero top."""
        surface, other = (-1, 0) if self._positive == "down" else (0, -1)

        if not (abs(B[surface] - 1.0) <= _B_TOLERANCE and abs(A[surface]) <= _AP_TOLERANCE):
            raise ValueError(
                "Cannot rebuild half level coefficients: the half level at the surface end "
                f"(positive={self._positive!r}, index {surface}) is not the surface (ap=0, b=1): "
                f"ap={A[surface]}, b={B[surface]}. The levels may be a subset of the model"
            )

        if top and not (abs(A[other]) <= _AP_TOLERANCE and abs(B[other]) <= _B_TOLERANCE):
            raise ValueError(
                "Cannot rebuild half level coefficients: the level numbers are unknown and the half level at "
                f"the other end (index {other}) is not a zero pressure model top (ap=0, b=0): "
                f"ap={A[other]}, b={B[other]}. The levels may be a subset of the model"
            )

    def _unknown_levels_evidence(self):
        """Return the half level ``(A, B)`` if the provisional numbering is supported, else raise ValueError.

        The evidence is: provisional numbering available, contiguous bounds, surface at the end given by
        ``positive`` and a zero pressure top at the other end.
        """
        if self._provisional is None:
            raise ValueError("Cannot rebuild half level coefficients: the level numbers are unknown")
        A, B = self._half_level_chain()
        self._check_ends(A, B, top=True)
        return A, B

    def _half_levels(self):
        """Return the half level ``(A, B)`` arrays or raise ValueError explaining why it is not possible."""
        if self._positive != "down":
            raise ValueError(
                f"Cannot rebuild half level coefficients: positive={self._positive!r}. The hybrid level type is "
                "positive down and the coefficients are ordered from the model top"
            )

        if self._ap_bnds is None:
            raise ValueError("Cannot rebuild half level coefficients: no bounds available")

        if self._levels is not None:
            n = len(self)
            if not np.array_equal(np.sort(self._levels), np.arange(1, n + 1)):
                raise ValueError(
                    f"Cannot rebuild half level coefficients: levels must be exactly 1..N, got {self._levels.tolist()}"
                )
            A, B = self._half_level_chain()
            self._check_ends(A, B, top=False)
            return A, B

        return self._unknown_levels_evidence()

    def can_rebuild_half_levels(self):
        """Return True if the half level ``A`` and ``B`` coefficients of the whole model can be rebuilt.

        The conservative completeness rule of the class applies: ``positive`` must be "down", the bounds
        must be available and contiguous in level order, the last half level must be the surface
        (``b == 1`` within 1e-9, ``ap == 0`` within 1e-6 Pa) and either the levels are known and are
        exactly ``1..n`` or (unknown levels in provisional numbering) the first half level is a zero
        pressure model top (``ap == 0`` and ``b == 0``, same tolerances). The contiguity comparison is
        :func:`numpy.allclose` with ``rtol=1e-12`` and ``atol=0``.
        """
        try:
            self._half_levels()
        except ValueError:
            return False
        return True

    def level_numbers(self):
        """Return the model level numbers of the levels, aligned with the array order of the object.

        Returns
        -------
        numpy.ndarray or None
            The known :attr:`levels` if they are known. Otherwise the provisional numbering
            (``1..n`` by ascending coordinate value when decoded with :meth:`from_xarray`) when the
            completeness evidence for unknown levels holds (contiguous bounds in level order, the surface at
            the end given by ``positive`` and a zero pressure model top at the other end), else None. This
            does not depend on whether the half level coefficients may be rebuilt: a complete
            positive-up model has level numbers although :meth:`to_level_parameters` raises.
        """
        if self._levels is not None:
            return self._levels
        try:
            self._unknown_levels_evidence()
        except ValueError:
            return None
        return self._provisional

    def to_level_parameters(self):
        """Return the half level coefficients of the whole model as a :class:`HybridLevelParameters`.

        Raises
        ------
        ValueError
            If the half level coefficients cannot be rebuilt, see :meth:`can_rebuild_half_levels` for the
            rule. The message tells which condition failed.
        """
        from earthkit.data.field.component.level_parameters import HybridLevelParameters

        A, B = self._half_levels()
        return HybridLevelParameters(A, B)

    def to_vertical(self, level):
        """Return the :class:`ParametricVertical` of a model level.

        Parameters
        ----------
        level: int
            Model level number. Must be one of the :meth:`level_numbers` of the object.

        Raises
        ------
        ValueError
            If ``level`` is not one of the levels or the half level coefficients cannot be rebuilt.
        """
        from earthkit.data.field.component.vertical import create_vertical

        A, B = self._half_levels()

        valid = self.level_numbers()
        try:
            ok = level == int(level) and int(level) in valid
        except (TypeError, ValueError):
            ok = False
        if not ok:
            raise ValueError(f"level={level!r} is not one of the levels {valid.tolist()}")

        return create_vertical({"level": int(level), "level_type": "hybrid", "coefficients": (A, B)})

    # ------------------------------------------------------------------
    # computation
    # ------------------------------------------------------------------

    def _p0_value(self, p0):
        p0 = self._p0 if p0 is None else p0
        try:
            valid = bool(np.isfinite(p0) and p0 > 0)
        except TypeError:
            valid = False
        if not valid:
            raise ValueError(f"p0={p0!r} is not a positive reference pressure, specify an explicit positive p0")
        return float(p0)

    def dimensionless_values(self, p0=None):
        """Return the dimensionless coordinate values ``ap / p0 + b``, shape ``(n,)``.

        Parameters
        ----------
        p0: float, optional
            Reference pressure (Pa). Default: :attr:`p0`.

        Raises
        ------
        ValueError
            If ``p0`` is not positive.
        """
        p0 = self._p0_value(p0)
        return self._ap / p0 + self._b

    def dimensionless_bounds(self, p0=None):
        """Return the bounds of the dimensionless coordinate values, shape ``(n, 2)``.

        Raises
        ------
        ValueError
            If ``p0`` is not positive or there are no bounds.
        """
        if self._ap_bnds is None:
            raise ValueError("No bounds available")
        p0 = self._p0_value(p0)
        return self._ap_bnds / p0 + self._b_bnds

    def pressure(self, ps):
        """Return the full level pressure ``ap + b * ps`` (Pa).

        Parameters
        ----------
        ps: float or array-like
            Surface pressure (Pa).

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n,) + np.shape(ps)``, with the level axis first.
        """
        ps = np.asarray(ps, dtype=np.float64)
        extra = (1,) * ps.ndim
        return self._ap.reshape((len(self),) + extra) + self._b.reshape((len(self),) + extra) * ps

    def half_level_pressure(self, ps):
        """Return the pressure on the half levels bounding each level, from the bounds.

        Parameters
        ----------
        ps: float or array-like
            Surface pressure (Pa).

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n, 2) + np.shape(ps)``.

        Raises
        ------
        ValueError
            If there are no bounds.
        """
        if self._ap_bnds is None:
            raise ValueError("No bounds available")
        ps = np.asarray(ps, dtype=np.float64)
        extra = (1,) * ps.ndim
        shape = (len(self), 2) + extra
        return self._ap_bnds.reshape(shape) + self._b_bnds.reshape(shape) * ps

    # ------------------------------------------------------------------
    # xarray
    # ------------------------------------------------------------------

    def encode(self, *, level_dim="level", coord_values="level_number", bounds=True, names=None, ps_dims=None):
        """Encode the coordinate into an :obj:`xarray.Dataset` following the CF conventions.

        The ``ap`` form of the formula is used: the pressure is ``ap(k) + b(k) * ps`` and the
        dimensionless coordinate value is ``ap(k) / p0 + b(k)``. By default the surface pressure variable is
        only referred to in ``formula_terms``, it is not written into the dataset (see ``ps_dims`` to
        write an all-NaN placeholder). When :attr:`p0` is
        positive and finite it is written as the scalar variable ``p0`` (units "Pa") and referred to by the
        ``p0`` term of the ``formula_terms`` of both the coordinate and its bounds, in both ``coord_values``
        modes, so that it is restored when the dataset is decoded. Otherwise neither the variable nor the
        term is written (and the decoded :attr:`p0` is the 100000 Pa default of the ``ap`` form).

        Parameters
        ----------
        level_dim: str
            Name of the level dimension and of the level coordinate variable.
        coord_values: str
            Values of the level coordinate. Possible values are:

            - "level_number": the model level numbers (int), the bounds are ``level - 0.5`` and
              ``level + 0.5`` in level order. The levels must be known. This is an ecosystem-compatibility
              mode (as used by cfgrib, CDO and the earthkit xarray engine), it does not follow the CF
              coordinate value semantics of a parametric vertical coordinate: the values are not the result
              of the formula. It is the only mode for a model with ``positive="up"``.
            - "dimensionless": the values ``ap / p0 + b`` and bounds ``ap_bnds / p0 + b_bnds`` (see
              :attr:`p0`, which must be positive). When the levels are known they are added as the
              auxiliary coordinate ``model_level_number``. The CF coordinate values must increase in the
              ``positive`` direction, i.e. with the level number, so the values must be strictly
              increasing with the level number (checked in level order, not in array order). This mode is
              strictly CF compliant.

            The ``positive`` attribute of the coordinate is the :attr:`positive` of the object.
        bounds: bool
            If True, write the bounds when the object has any. No error is raised when
            there are no bounds.
        names: dict, optional
            Overrides the default names. The valid keys and their defaults are: "ap" (``"ap"``),
            "b" (``"b"``), "ap_bnds" (``"ap_bnds"``), "b_bnds" (``"b_bnds"``), "ps" (:attr:`ps_name`,
            None: no ``ps`` term is written), "p0" (``"p0"``), "level_bnds" (``"<level_dim>_bnds"``),
            "bnds" (``"bnds"``, bounds dimension) and
            "level_number" (``"model_level_number"``, only used with "dimensionless").
        ps_dims: dict, optional
            Mapping from dimension name to size. When specified, the surface pressure is written as a
            float64 placeholder variable named by the "ps" name with these dimensions (in the given order),
            with all the values NaN and the attributes ``standard_name="surface_air_pressure"``,
            ``units="Pa"`` and ``long_name="surface air pressure"``. The values are a read-only broadcast
            view of a single NaN (:func:`numpy.broadcast_to`), so the placeholder needs no memory
            until the dataset is copied or written. The dimensions must not be those of any other
            variable written here (see ``Raises``). An empty mapping writes a scalar.

        Returns
        -------
        xarray.Dataset
            Dataset with the level coordinate ``level_dim``, the variables ``ap`` and ``b`` and, when
            bounds are written, ``ap_bnds``, ``b_bnds`` and the level bounds variable. When ``ps_dims``
            is specified the ``ps`` placeholder is included. The levels are written in ascending level
            number order (the known levels, else the provisional numbering, which is the array order for
            an object created directly with unknown levels); the bounds are in level order.

        Raises
        ------
        ValueError
            If ``ps_dims`` is specified but the "ps" name is None, a name in ``ps_dims`` is not a non-empty str, a
            size is not a non-negative int or a name in ``ps_dims`` is the same as a written name (the level
            dimension, any written variable, the bounds dimension when bounds are written or the "ps" name).
            Also if ``coord_values`` is invalid, ``names`` has unknown keys, a name (including that of ``ps``
            and ``p0``) is the same as another written name or dimension, the levels
            are unknown with ``coord_values="level_number"``, or with ``coord_values="dimensionless"``
            :attr:`p0` is not positive or the dimensionless values do not strictly increase with the
            level number.
        """
        import xarray as xr

        from .formula_terms import format_formula_terms

        if coord_values not in ("level_number", "dimensionless"):
            raise ValueError(f"coord_values must be 'level_number' or 'dimensionless', got {coord_values!r}")

        if not isinstance(level_dim, str) or not level_dim:
            raise ValueError(f"level_dim must be a non-empty str, got {level_dim!r}")

        nm = {
            "ap": "ap",
            "b": "b",
            "ap_bnds": "ap_bnds",
            "b_bnds": "b_bnds",
            "ps": self._ps_name,  # None: no ps term is written
            "p0": "p0",
            "level_bnds": f"{level_dim}_bnds",
            "bnds": "bnds",
            "level_number": "model_level_number",
        }
        if names:
            unknown = [k for k in names if k not in nm]
            if unknown:
                raise ValueError(f"Unknown keys in names: {unknown}. Valid keys: {list(nm)}")
            nm.update(names)

        for k, v in nm.items():
            if (v is not None or k != "ps") and (not isinstance(v, str) or not v):
                raise ValueError(f"names[{k!r}] must be a non-empty str, got {v!r}")

        if self._levels is None and coord_values == "level_number":
            raise ValueError("Cannot use coord_values='level_number': the levels are unknown")

        with_bounds = bool(bounds) and self._ap_bnds is not None

        # a scalar p0 variable is only written when the reference pressure is a valid one
        with_p0 = bool(np.isfinite(self._p0) and self._p0 > 0)

        # variables that will be written must have distinct names. The surface pressure variable
        # is not written but it is referred to, so its name must not be one of the others either
        used = [level_dim, nm["ap"], nm["b"]]
        if with_bounds:
            used += [nm["ap_bnds"], nm["b_bnds"], nm["level_bnds"], nm["bnds"]]
        if coord_values == "dimensionless" and self._levels is not None:
            used.append(nm["level_number"])
        if with_p0:
            used.append(nm["p0"])
        if nm["ps"] is not None:
            used.append(nm["ps"])
        if len(set(used)) != len(used):
            raise ValueError(f"The names of the variables and dimensions must be distinct, got {used}")

        ps_shape = None
        if ps_dims is not None:
            if nm["ps"] is None:
                raise ValueError("ps_dims is specified but the ps name is None")
            try:
                ps_dims = dict(ps_dims)
            except (TypeError, ValueError) as e:
                raise ValueError(f"ps_dims must be a mapping from dimension name to size: {e}") from e
            for d, size in ps_dims.items():
                if not isinstance(d, str) or not d:
                    raise ValueError(f"Invalid dimension name in ps_dims: {d!r}")
                if isinstance(size, bool) or not isinstance(size, (int, np.integer)) or size < 0:
                    raise ValueError(f"Invalid size for dimension {d!r} in ps_dims: {size!r}")
                if d in used:
                    raise ValueError(f"The dimension {d!r} of ps_dims is the same as a written name, got {used}")
            ps_shape = tuple(int(s) for s in ps_dims.values())

        # everything is written in level order (the known levels, else the provisional numbering, else the
        # array order), so that the coordinate values and the bounds follow the level numbers
        order = self._level_order()
        if order is None:
            order = np.arange(len(self))

        ap = self._ap[order]
        b = self._b[order]
        levels = None if self._levels is None else self._levels[order]
        ap_bnds = self._ap_bnds[order] if with_bounds else None
        b_bnds = self._b_bnds[order] if with_bounds else None

        if coord_values == "level_number":
            values = levels.astype(np.int64)
            level_bnds = levels[:, None].astype(np.float64) + np.array([-0.5, 0.5]) if with_bounds else None
        else:
            values = ap / self._p0_value(None) + b
            level_bnds = ap_bnds / self._p0_value(None) + b_bnds if with_bounds else None
            # CF: the coordinate values increase in the positive direction, i.e. with the level number
            if len(values) > 1 and not np.all(np.diff(values) > 0):
                raise ValueError(
                    "The dimensionless coordinate values do not strictly increase with the level number "
                    f"(positive={self._positive!r}). Use coord_values='level_number'"
                )

        terms = {"ap": nm["ap"], "b": nm["b"]}
        if nm["ps"] is not None:
            terms["ps"] = nm["ps"]
        if with_p0:
            terms["p0"] = nm["p0"]
        coord_attrs = {
            "standard_name": self.STANDARD_NAME,
            "long_name": "hybrid level",
            "units": "1",
            "positive": self._positive,
            "axis": "Z",
            "computed_standard_name": self.COMPUTED_STANDARD_NAME,
            "formula_terms": format_formula_terms(terms, order=("ap", "b", "ps", "p0")),
        }

        data_vars = {
            nm["ap"]: ((level_dim,), ap, {"long_name": "vertical coordinate formula term: ap(k)", "units": "Pa"}),
            nm["b"]: ((level_dim,), b, {"long_name": "vertical coordinate formula term: b(k)", "units": "1"}),
        }

        if with_p0:
            data_vars[nm["p0"]] = (
                (),
                np.float64(self._p0),
                {
                    "units": "Pa",
                    "standard_name": "reference_air_pressure_for_atmosphere_vertical_coordinate",
                    "long_name": "vertical coordinate formula term: reference pressure",
                },
            )

        if ps_shape is not None:
            data_vars[nm["ps"]] = (
                tuple(ps_dims),
                np.broadcast_to(np.float64(np.nan), ps_shape),
                {
                    "standard_name": "surface_air_pressure",
                    "units": "Pa",
                    "long_name": "surface air pressure",
                },
            )

        if with_bounds:
            bdims = (level_dim, nm["bnds"])
            coord_attrs["bounds"] = nm["level_bnds"]
            bterms = {"ap": nm["ap_bnds"], "b": nm["b_bnds"]}
            if nm["ps"] is not None:
                bterms["ps"] = nm["ps"]
            if with_p0:
                bterms["p0"] = nm["p0"]
            data_vars[nm["ap_bnds"]] = (
                bdims,
                ap_bnds,
                {"long_name": "vertical coordinate formula term: ap(k+1/2)", "units": "Pa"},
            )
            data_vars[nm["b_bnds"]] = (
                bdims,
                b_bnds,
                {"long_name": "vertical coordinate formula term: b(k+1/2)", "units": "1"},
            )
            data_vars[nm["level_bnds"]] = (
                bdims,
                level_bnds,
                {"formula_terms": format_formula_terms(bterms, order=("ap", "b", "ps", "p0"))},
            )

        coords = {level_dim: ((level_dim,), values, coord_attrs)}
        if coord_values == "dimensionless" and levels is not None:
            coords[nm["level_number"]] = (
                (level_dim,),
                levels.astype(np.int64),
                {"standard_name": "model_level_number", "long_name": "model level number", "units": "1"},
            )

        ds = xr.Dataset(data_vars=data_vars, coords=coords)

        # CF: coordinate and bounds variables must not have a _FillValue
        for var in ds.variables.values():
            var.encoding["_FillValue"] = None

        return ds

    @classmethod
    def from_xarray(cls, ds, coord_name):
        """Create the object from the coordinate ``coord_name`` of ``ds``.

        The coordinate must have a ``formula_terms`` attribute. Two forms of the formula are
        accepted: the ``ap`` form (terms ``ap``, ``b``, ``ps``) and the ``a`` form (terms ``a``, ``b``,
        ``ps``, ``p0``), where ``ap = a * p0``. ``a`` and ``b`` must be dimensionless (units absent,
        "" or "1"); ``ap`` and ``p0`` must be pressures (units "Pa" or "hPa", absent units are
        taken as "Pa"). The ``ps`` variable is not read, only its name is kept as ``ps_name``.

        Omitted terms are zero as in the CF conventions: without ``b``, ``b`` is zero; without ``a``
        and ``ap``, ``ap`` is zero; with ``a`` but no ``p0``, ``ap`` is zero. The :attr:`p0` of the
        object is the value of the ``p0`` variable when there is a ``p0`` term (it is valid in both
        forms). Without a ``p0`` term it is 0 in the ``a`` form (the reference pressure is unknown, so
        :meth:`dimensionless_values` requires an explicit ``p0``) and the default 100000 Pa in the
        ``ap`` form (CMIP convention). An omitted term in the bounds only is not accepted (ValueError).

        The ``formula_terms`` and ``bounds`` attributes are also found when they are in the
        ``encoding`` of the variables, where :func:`xarray.decode_cf` and :func:`xarray.open_dataset`
        with ``decode_coords="all"`` move them.

        If the coordinate has a ``bounds`` attribute, the bounds variable must have its own
        ``formula_terms`` with the same ``ps`` and ``p0`` as the coordinate and refer to 2D term
        variables with a dimension of size 2. If the bounds variable has no ``formula_terms`` (or does not exist)
        the object is created without bounds and a warning is logged.

        The ``positive`` attribute of the coordinate (also looked up in the encoding) gives the
        :attr:`positive` of the object ("down" or "up", case-insensitive); when it is missing "down" is
        used and a debug message is logged. The CF coordinate values increase in the ``positive``
        direction, so the level numbers increase with the coordinate values. The two vertices of each
        cell of the bounds are put in level order using the values of the level bounds variable
        (ascending), and the term bounds are reordered the same way, so the bounds may be stored in either
        vertex order. The arrays of the object keep the order of the dataset.

        The level numbers are taken from the variable with ``standard_name="model_level_number"`` on
        the same dimension as the coordinate. When there is none, they are taken from the
        coordinate values if they are all integers >= 1 and unique, otherwise they are unknown
        (:attr:`levels` is None). Unknown levels are numbered provisionally ``1..n`` by ascending
        coordinate value (whatever the order of the dataset), which :meth:`level_numbers` returns
        when the completeness evidence holds (see the class).

        Parameters
        ----------
        ds: xarray.Dataset
            The dataset.
        coord_name: str
            Name of the coordinate variable.

        Raises
        ------
        ValueError
            If the coordinate is not found, is not 1D or has no valid ``formula_terms``, a term
            variable is missing, has invalid dimensions, shape or units, both ``a`` and ``ap`` are
            specified, the ``ps``/``p0`` terms of the bounds differ from those of the coordinate, the
            level bounds variable is not a finite numeric array of shape ``(n, 2)`` or the ``positive``
            attribute is neither "down" nor "up".
        """
        from .formula_terms import parse_formula_terms

        if coord_name not in ds.variables:
            raise ValueError(f"Variable {coord_name!r} not found in dataset")

        coord = ds.variables[coord_name]
        formula_terms = get_cf_attribute(coord, "formula_terms")
        if formula_terms is None:
            raise ValueError(f"Variable {coord_name!r} has no formula_terms attribute")

        if coord.ndim != 1:
            raise ValueError(f"Variable {coord_name!r} must be 1D, got dims {coord.dims}")

        positive = get_cf_attribute(coord, "positive")
        if positive is None:
            LOG.debug("Variable %r has no positive attribute, taking it as 'down'", coord_name)
            positive = "down"
        else:
            positive = _as_positive(positive, f"The positive attribute of {coord_name!r}")

        dim = coord.dims[0]
        n = coord.shape[0]

        terms = parse_formula_terms(formula_terms)
        _check_terms(terms, cls.TERMS, coord_name)
        ap, b, p0 = _decode_terms(ds, terms, dim, n, False)

        ap_bnds = b_bnds = None
        bnds_name = get_cf_attribute(coord, "bounds")
        if bnds_name:
            if bnds_name not in ds.variables:
                LOG.warning("Bounds variable %r of %r not found in dataset, bounds are ignored", bnds_name, coord_name)
            else:
                bnds_ft = get_cf_attribute(ds.variables[bnds_name], "formula_terms")
                if bnds_ft is None:
                    LOG.warning(
                        "Bounds variable %r of %r has no formula_terms, bounds are ignored", bnds_name, coord_name
                    )
                else:
                    bterms = parse_formula_terms(bnds_ft)
                    _check_terms(bterms, cls.TERMS, bnds_name)
                    for t in ("ps", "p0"):
                        if bterms.get(t) != terms.get(t):
                            raise ValueError(
                                f"The {t!r} term of the bounds variable {bnds_name!r} ({bterms.get(t)!r}) differs "
                                f"from that of {coord_name!r} ({terms.get(t)!r})"
                            )
                    for what, keys in (("a/ap", ("a", "ap")), ("b", ("b",))):
                        if any(k in terms for k in keys) != any(k in bterms for k in keys):
                            raise ValueError(
                                f"The {what} term is specified for only one of {coord_name!r} and {bnds_name!r}"
                            )
                    ap_bnds, b_bnds, _ = _decode_terms(ds, bterms, dim, n, True)

                    # put the two vertices of each cell in level order: ascending values of the level bounds
                    # (the CF coordinate values increase with the level number)
                    level_bnds = _read_level_bounds(ds, bnds_name, dim, n)
                    swap = (level_bnds[:, 0] > level_bnds[:, 1])[:, None]
                    if swap.any():
                        ap_bnds = np.where(swap, ap_bnds[:, ::-1], ap_bnds)
                        b_bnds = np.where(swap, b_bnds[:, ::-1], b_bnds)

        levels = _find_levels(ds, coord, dim)

        if p0 is not None:
            kwargs = {"p0": p0}
        elif "a" in terms:
            # the reference pressure is unknown: ap was taken as zero, no positive p0 can be assumed
            kwargs = {"p0": 0.0}
        else:
            kwargs = {}
        result = cls(
            ap,
            b,
            ap_bnds=ap_bnds,
            b_bnds=b_bnds,
            levels=levels,
            ps_name=terms.get("ps"),
            positive=positive,
            **kwargs,
        )

        if levels is None:
            # provisional numbering by ascending coordinate value, the arrays keep the dataset order
            result._provisional = _provisional_numbering(coord)

        return result


def _check_terms(terms, valid, name):
    unknown = [t for t in terms if t not in valid]
    if unknown:
        raise ValueError(f"Unknown formula_terms {unknown} in {name!r}, valid terms are {list(valid)}")

    if "a" in terms and "ap" in terms:
        raise ValueError(f"formula_terms of {name!r} must not contain both 'a' and 'ap'")


def _get_variable(ds, varname, term):
    if varname not in ds.variables:
        raise ValueError(f"Variable {varname!r} of formula term {term!r} not found in dataset")
    return ds.variables[varname]


def _units_factor(var, varname, term, pressure):
    """Return the factor converting the values of ``var`` to Pa (pressure) or to dimensionless."""
    units = var.attrs.get("units")
    if units is not None:
        units = str(units).strip()

    if pressure:
        if units is None or units == "Pa":
            return 1.0
        if units == "hPa":
            return 100.0
        raise ValueError(
            f"Variable {varname!r} of formula term {term!r} must have pressure units (Pa or hPa), got {units!r}"
        )

    if units in (None, "", "1"):
        return 1.0
    raise ValueError(f"Variable {varname!r} of formula term {term!r} must be dimensionless, got units {units!r}")


def _read_values(var, varname, term):
    try:
        values = np.asarray(var.values, dtype=np.float64)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Variable {varname!r} of formula term {term!r} is not numeric: {e}") from e
    if not np.all(np.isfinite(values)):
        raise ValueError(f"Variable {varname!r} of formula term {term!r} has missing or non-finite values")
    return values


def _read_term(ds, varname, term, dim, n, bounds, pressure):
    """Read a term variable as an array of shape ``(n,)`` or ``(n, 2)`` (bounds), converted to Pa if a pressure."""
    var = _get_variable(ds, varname, term)
    factor = _units_factor(var, varname, term, pressure)

    if bounds:
        if var.ndim != 2 or dim not in var.dims:
            raise ValueError(
                f"Bounds variable {varname!r} of formula term {term!r} must be 2D with dimension {dim!r}, "
                f"got dims {var.dims}"
            )
        if var.dims[0] != dim:
            var = var.transpose(dim, ...)
        shape = (n, 2)
    else:
        if var.dims != (dim,):
            raise ValueError(
                f"Variable {varname!r} of formula term {term!r} must be 1D with dimension {dim!r}, got dims {var.dims}"
            )
        shape = (n,)

    values = _read_values(var, varname, term)
    if values.shape != shape:
        raise ValueError(f"Variable {varname!r} of formula term {term!r} must have shape {shape}, got {values.shape}")

    return values * factor


def _read_p0(ds, varname):
    var = _get_variable(ds, varname, "p0")
    factor = _units_factor(var, varname, "p0", True)
    if var.size != 1:
        raise ValueError(f"Variable {varname!r} of formula term 'p0' must be a scalar, got dims {var.dims}")
    value = float(_read_values(var, varname, "p0").reshape(-1)[0]) * factor
    if not value > 0:
        raise ValueError(f"Variable {varname!r} of formula term 'p0' must be positive, got {value}")
    return value


def _decode_terms(ds, terms, dim, n, bounds):
    """Return ``(ap, b, p0)`` from the formula terms. ``p0`` is None when there is no ``p0`` term."""
    shape = (n, 2) if bounds else (n,)

    p0 = _read_p0(ds, terms["p0"]) if "p0" in terms else None

    if "ap" in terms:
        ap = _read_term(ds, terms["ap"], "ap", dim, n, bounds, True)
    elif "a" in terms:
        a = _read_term(ds, terms["a"], "a", dim, n, bounds, False)
        if p0 is None:
            LOG.warning("Formula term 'a' used without 'p0': ap is taken as zero")
            ap = np.zeros(shape)
        else:
            ap = a * p0
    else:
        ap = np.zeros(shape)

    if "b" in terms:
        b = _read_term(ds, terms["b"], "b", dim, n, bounds, False)
    else:
        b = np.zeros(shape)

    return ap, b, p0


def _read_level_bounds(ds, varname, dim, n):
    """Read the level bounds variable as an array of shape ``(n, 2)`` (``dim`` first)."""
    var = _get_variable(ds, varname, "bounds")
    if var.ndim != 2 or dim not in var.dims:
        raise ValueError(f"Level bounds variable {varname!r} must be 2D with dimension {dim!r}, got dims {var.dims}")
    if var.dims[0] != dim:
        var = var.transpose(dim, ...)

    values = _read_values(var, varname, "bounds")
    if values.shape != (n, 2):
        raise ValueError(f"Level bounds variable {varname!r} must have shape {(n, 2)}, got {values.shape}")
    return values


def _provisional_numbering(coord):
    """Return the ranks ``1..n`` of the coordinate values (ascending), or None if they are not usable."""
    try:
        values = np.asarray(coord.values, dtype=np.float64)
    except (TypeError, ValueError):
        return None

    if not np.all(np.isfinite(values)) or len(np.unique(values)) != len(values):
        return None

    ranks = np.empty(len(values), dtype=np.int64)
    ranks[np.argsort(values, kind="stable")] = np.arange(1, len(values) + 1)
    ranks.setflags(write=False)
    return ranks


def _find_levels(ds, coord, dim):
    # explicit level number coordinate on the same dimension
    for name, var in ds.variables.items():
        if var.attrs.get("standard_name") == "model_level_number" and var.dims == (dim,):
            return _as_levels(_read_values(var, name, "model_level_number"), name)

    try:
        values = np.asarray(coord.values, dtype=np.float64)
        if np.all(np.isfinite(values)) and np.all(values == np.round(values)) and np.all(values >= 1):
            return _as_levels(values)
    except (TypeError, ValueError):
        pass

    return None
