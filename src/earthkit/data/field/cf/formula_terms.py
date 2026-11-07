# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Helpers for the CF ``formula_terms`` attribute and the CF-1.13 parametric vertical coordinates."""

import re

# Terms of all the parametric vertical coordinates defined in CF-1.13 (Appendix D), keyed by
# standard name. Term names are always lower case.
CF_PARAMETRIC_VERTICAL_TERMS = {
    "atmosphere_ln_pressure_coordinate": ("p0", "lev"),
    "atmosphere_sigma_coordinate": ("sigma", "ps", "ptop"),
    "atmosphere_hybrid_sigma_pressure_coordinate": ("a", "b", "ps", "p0", "ap"),
    "atmosphere_hybrid_height_coordinate": ("a", "b", "orog"),
    "atmosphere_sleve_coordinate": ("a", "b1", "b2", "ztop", "zsurf1", "zsurf2"),
    "ocean_sigma_coordinate": ("sigma", "eta", "depth"),
    "ocean_s_coordinate": ("s", "eta", "depth", "a", "b", "depth_c"),
    "ocean_s_coordinate_g1": ("s", "c", "eta", "depth", "depth_c"),
    "ocean_s_coordinate_g2": ("s", "c", "eta", "depth", "depth_c"),
    # "nsigma" is deprecated
    "ocean_sigma_z_coordinate": ("sigma", "eta", "depth", "depth_c", "nsigma", "zlev"),
    "ocean_double_sigma_coordinate": ("sigma", "depth", "z1", "z2", "a", "href", "k_c"),
}

_COLON_RE = re.compile(r"\s*:\s*")


def parse_formula_terms(s):
    """Parse a CF ``formula_terms`` string.

    Parameters
    ----------
    s: str
        String made of ``term: variable`` pairs, e.g. ``"a: hyam b: hybm p0: P0 ps: PS"``.
        Spaces around the colons are optional.

    Returns
    -------
    dict
        Mapping from the (lower-cased) term name to the variable name. The variable names
        are kept as they are. The order of the terms in ``s`` is preserved.

    Raises
    ------
    ValueError
        If ``s`` is empty or malformed (dangling term, token without a term) or when a term
        is specified more than once (term names are case-insensitive).
    """
    if not isinstance(s, str):
        raise ValueError(f"formula_terms must be a str, got {type(s)}")

    tokens = _COLON_RE.sub(":", s.strip()).split()
    if not tokens:
        raise ValueError(f"Empty formula_terms: {s!r}")

    result = {}
    for token in tokens:
        parts = token.split(":")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"Malformed formula_terms {s!r}: invalid token {token!r}")
        term, var = parts
        term = term.lower()
        if term in result:
            raise ValueError(f"Malformed formula_terms {s!r}: duplicate term {term!r}")
        result[term] = var

    return result


def format_formula_terms(terms, order=None):
    """Format a term to variable mapping into a CF ``formula_terms`` string.

    Parameters
    ----------
    terms: dict
        Mapping from the term name to the variable name.
    order: iterable of str, optional
        Fixes the order of the terms in the output. Terms not listed in ``order`` are
        appended in insertion order. Names in ``order`` that are not in ``terms`` are ignored.
        By default the insertion order of ``terms`` is used.

    Returns
    -------
    str
        String such as ``"ap: ap b: b ps: ps"``.
    """
    if order is None:
        keys = list(terms)
    else:
        keys = [k for k in order if k in terms]
        keys += [k for k in terms if k not in keys]

    return " ".join(f"{k}: {terms[k]}" for k in keys)
