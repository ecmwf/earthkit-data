# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import itertools
import logging
import os
import re
from functools import cached_property
from pathlib import Path
from typing import Any as TypingAny
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from .dates import to_datetime
from .dates import to_timedelta

LOG = logging.getLogger(__name__)

RE1 = re.compile(r"{([^}]*)}")
RE2 = re.compile(r"\(([^}]*)\)")


class Any:
    """Represents a type that accepts any value."""

    def substitute(self, value: TypingAny, name: str) -> TypingAny:
        """Substitute the value without any validation.

        Parameters
        ----------
        value : Any
            The value to substitute.
        name : str
            The name of the parameter.

        Returns
        -------
        Any
            The substituted value.
        """
        return value


class Enum:
    """Represents a type that accepts a value from a predefined set of strings.

    Parameters
    ----------
    enum : str, optional
        Comma-separated string of allowed values, by default "".
    """

    def __init__(self, enum: str = "") -> None:
        self.enum: set[str] = set(enum.split(","))

    def substitute(self, value: str, name: str) -> str:
        """Substitute the value if it is in the predefined set.

        Parameters
        ----------
        value : str
            The value to substitute.
        name : str
            The name of the parameter.

        Returns
        -------
        str
            The substituted value.

        Raises
        ------
        ValueError
            If the value is not in the predefined set.
        """
        if self.enum and value not in self.enum:
            raise ValueError(
                "Invalid value '{}' for parameter '{}', expected one of {}".format(value, name, self.enum)
            )
        return value


class Int:
    """Represents a type that accepts integer values.

    Parameters
    ----------
    format : str, optional
        Format string for integer substitution, by default "%d".
    """

    def __init__(self, format: str = "%d") -> None:
        self.format: str = format

    def substitute(self, value: int, name: str) -> str:
        """Substitute the value if it is an integer.

        Parameters
        ----------
        value : int
            The value to substitute.
        name : str
            The name of the parameter.

        Returns
        -------
        str
            The substituted value.

        Raises
        ------
        ValueError
            If the value is not an integer.
        """
        if not isinstance(value, int):
            raise ValueError("Invalid value '{}' for parameter '{}', expected an integer".format(value, name))
        return self.format % value


class Float:
    """Represents a type that accepts float values.

    Parameters
    ----------
    format : str, optional
        Format string for float substitution, by default "%g".
    """

    def __init__(self, format: str = "%g") -> None:
        self.format: str = format

    def substitute(self, value: Union[int, float], name: str) -> str:
        """Substitute the value if it is a float or integer.

        Parameters
        ----------
        value : int or float
            The value to substitute.
        name : str
            The name of the parameter.

        Returns
        -------
        str
            The substituted value.

        Raises
        ------
        ValueError
            If the value is not a float or integer.
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Invalid value '{}' for parameter '{}', expected a float".format(value, name))

        return self.format % value


class Datetime:
    """Represents a type that accepts datetime values.

    Parameters
    ----------
    format : str
        Format string for datetime substitution.
    """

    def __init__(self, format: str) -> None:
        self.format: str = format

    def substitute(self, value: TypingAny, name: str) -> str:
        """Substitute the value as a formatted datetime string.

        Parameters
        ----------
        value : Any
            The value to substitute.
        name : str
            The name of the parameter.

        Returns
        -------
        str
            The substituted datetime string.
        """
        return to_datetime(value).strftime(self.format)


class DatetimeDelta:
    """Represents a type that accepts datetime deltas.

    Parameters
    ----------
    params : str
        Parameters for delta and format, separated by a semicolon.

    Attributes
    ----------
    delta : str
        Timedelta string for datetime substitution. Accepted formats use the following suffixes:
        - "h" for hours (the default)
        - "m" for minutes
        - "s" for seconds

    format : str
        Format string for datetime substitution.
    """

    def __init__(self, params: str) -> None:
        params_list = params.split(";")
        if len(params_list) != 2:
            raise ValueError(
                "Invalid parameters '{}' for class DatetimeDelta, expected (delta;format)".format(params)
            )
        self.delta = params_list[0].strip()
        self.format = params_list[1].strip()

    def substitute(self, value: TypingAny, name: str) -> str:
        """Substitute the datetime value, add the delta and format the result.

        Parameters
        ----------
        value : Any
            The value to substitute. Must be convertible to a datetime object.
        name : str
            The name of the parameter.

        Returns
        -------
        str
            The substituted datetime value with the delta added to it and formatted.

        Raises
        ------
        ValueError
            If the delta format is invalid.
        """
        sign = -1 if self.delta[0] == "-" else 1
        if re.fullmatch(r"[-\+]?\d+[hms]?", self.delta):
            delta = re.search(r"\d+[hms]?", self.delta).group(0)
        else:
            raise ValueError(
                "Invalid value '{}' for delta, expected time in hour (h), minute (m) or second (s)".format(
                    self.delta
                )
            )

        valid_date = to_datetime(value) + sign * to_timedelta(delta)
        return valid_date.strftime(self.format)


class Str:
    """Represents a type that accepts string values.

    Parameters
    ----------
    format : str, optional
        Format string for string substitution, by default "%s".
    """

    def __init__(self, format: str = "%s") -> None:
        self.format: str = format

    def substitute(self, value: str, name: str) -> str:
        """Substitute the value if it is a string.

        Parameters
        ----------
        value : str
            The value to substitute.
        name : str
            The name of the parameter.

        Returns
        -------
        str
            The substituted value.

        Raises
        ------
        ValueError
            If the value is not a string.
        """
        if not isinstance(value, str):
            raise ValueError("Invalid value '{}' for parameter '{}', expected a string".format(value, name))
        return self.format % value


TYPES = {
    "": Any,
    "int": Int,
    "float": Float,
    "date": Datetime,
    "strftime": Datetime,
    "strftimedelta": DatetimeDelta,
    "enum": Enum,
}


class Constant:
    """Represents a constant value in a pattern.

    Parameters
    ----------
    value : Any
        The constant value.
    """

    name: Optional[str] = None

    def __init__(self, value: TypingAny) -> None:
        self.value: TypingAny = value

    def substitute(self, params: Dict[str, TypingAny], **kwargs: TypingAny) -> TypingAny:
        """Substitute the constant value.

        Parameters
        ----------
        params : dict
            Parameters to substitute (not used for constants).

        Returns
        -------
        Any
            The constant value.
        """
        return self.value

    def substitute_many(self, params: Dict[str, TypingAny], **kwargs: TypingAny) -> TypingAny:
        return [self.value]

    def pattern(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value})"


class Variable:
    """Represents a variable in a pattern.

    Parameters
    ----------
    value : str
        The variable definition string.
    """

    def __init__(self, value: str) -> None:
        bits = value.split(":")
        self.name = bits[0]
        kind = RE2.split(":".join(bits[1:]))
        if len(kind) == 1:
            self.kind = TYPES[kind[0]]()
        else:
            self.kind = TYPES[kind[0]](kind[1])

        self.value = value

    def substitute(self, params: Dict[str, TypingAny]) -> TypingAny:
        """Substitute value for a parameter.

        Parameters
        ----------
        params : dict
            The value belonging to ``self.name`` in ``params`` are
            substituted into the Variable. The value to substitute must be a
            single value.

        Returns
        -------
            Substituted value.

        Raises
        ------
        ValueError
            If ``self.name`` is not in ``params``.

        Example
        -------
        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute({"my_date": "2000-01-01"})
        '2000-01-01'

        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute({"level": "500"})
        ValueError: Missing parameter 'my_date'
        """
        if self.name in params:
            return self.kind.substitute(params[self.name], self.name)
        else:
            raise ValueError("Missing parameter '{}'".format(self.name))

    def substitute_many(self, params: Dict[str, TypingAny]) -> Optional[List[TypingAny]]:
        """Substitute all values for a parameter.

        Parameters
        ----------
        params : dict
            The values belonging to ``self.name`` in ``params`` are
            substituted into the Variable.

        Returns
        -------
        list
            List of substituted values.
        Raises
        ------
        ValueError
            If ``self.name`` is not in ``params``.


        Example
        -------
        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute_many({"my_date": ["2000-01-01", "2000-01-02"]})
        ['2000-01-01', '2000-01-02']

        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute_many({"my_date": "2000-01-01"})
        ['2000-01-01']

        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute_many({"level": "500"})
        ValueError: Missing parameter 'my_date'
        """
        if self.name in params:
            v = params[self.name]
            if not isinstance(v, list):
                v = [v]
            return [self.kind.substitute(x, self.name) for x in v]
        else:
            raise ValueError("Missing parameter '{}'".format(self.name))

    def pattern(self) -> str:
        return "{" + self.value + "}"

    def __repr__(self) -> str:
        return f"Variable({self.name},{self.value},{self.kind})"


FUNCTIONS = dict(lower=lambda s: s.lower())


class Function:
    """Represents a function applied to a variable in a pattern.

    Parameters
    ----------
    value : str
        The function definition string.
    """

    def __init__(self, value: str) -> None:
        functions = value.split("|")
        self.name = functions[0]
        self.variable = Variable(functions[0])
        self.functions = functions[1:]
        self._pattern = value

    def substitute(self, params: Dict[str, TypingAny], **kwargs: TypingAny) -> TypingAny:
        """Substitute the variable and apply functions.

        Parameters
        ----------
        params : dict
            Parameters to substitute.

        Returns
        -------
        Any
            The substituted and transformed value.
        """
        value = self.variable.substitute(params, **kwargs)
        for f in self.functions:
            value = FUNCTIONS[f](value)
        return value

    def substitute_many(self, params: Dict[str, TypingAny], **kwargs: TypingAny) -> TypingAny:
        value = self.variable.substitute_many(params, **kwargs)
        res = []
        for f in self.functions:
            for v in value:
                res.append(FUNCTIONS[f](v))
        return res

    def pattern(self) -> str:
        return self._pattern


class Pattern:
    """Represents a pattern with variables and constants.

    Parameters
    ----------
    pattern : str
        The pattern string.
    """

    def __init__(self, pattern: str) -> None:
        self.pattern = []
        self.variables = []
        for i, p in enumerate(RE1.split(pattern)):
            if i % 2 == 0:
                if p != "":
                    self.pattern.append(Constant(p))
            else:
                if "|" in p:
                    v = Function(p)
                else:
                    v = Variable(p)
                self.variables.append(v)
                self.pattern.append(v)

    @property
    def names(self) -> List[str]:
        return sorted({v.name for v in self.variables})

    def is_constant(self) -> bool:
        return not self.variables and len(self.pattern) == 1 and isinstance(self.pattern[0], Constant)

    def substitute(
        self,
        *args: Tuple[Dict[str, TypingAny]],
        allow_extra: bool = False,
        **kwargs: TypingAny,
    ) -> Union[str, List[str]]:
        """Substitute values into the pattern.

        Parameters
        ----------
        args : tuple of dict
            Positional dictionaries of parameters to substitute.
        allow_extra : bool, optional
            Whether to allow using input with parameters not part of the Pattern.
        kwargs : dict
            Additional keyword arguments for substitution.

        Returns
        -------
        str or list
            The substituted pattern as a string or list of strings.

        Raises
        ------
        ValueError
            If there are unused parameters and `allow_extra` is False.
        """
        params = {}
        for a in args:
            params.update(a)
        params.update(kwargs)

        for k, v in params.items():
            if isinstance(v, list):
                return self._substitute_many(params, allow_extra=allow_extra)

        return self._substitute_one(params, allow_extra=allow_extra)

    def _substitute_one(
        self,
        params: Dict[str, TypingAny],
        allow_extra: bool = False,
    ) -> str:
        used = set(params.keys())
        result = []
        for p in self.pattern:
            used.discard(p.name)
            result.append(p.substitute(params))
        if used and not allow_extra:
            raise ValueError("Unused parameter(s): {}".format(used))

        return "".join(str(x) for x in result)

    def _substitute_many(
        self,
        params: Dict[str, TypingAny],
        allow_extra: bool = False,
    ) -> List[str]:
        for k, v in list(params.items()):
            if not isinstance(v, list):
                params[k] = [v]

        seen = set()
        result = []
        for n in (dict(zip(params.keys(), x)) for x in itertools.product(*params.values())):
            m = self.substitute(n, allow_extra=allow_extra)
            if m not in seen:
                seen.add(m)
                result.append(m)

        return result

    def _subpattern(self, params: Dict[str, TypingAny]) -> str:
        """Substitute the pattern with the given parameters.

        Parameters
        ----------
        params : dict
            The parameters to substitute. Each parameter must be a single value.

        Returns
        -------
        str
            The substituted pattern.
        """
        result = []
        for p in self.pattern:
            try:
                result.append(p.substitute(params))
            except ValueError:
                result.append(p.pattern())

        return "".join(str(x) for x in result)

    def match(self, value: str) -> Optional[re.Match]:
        """Match pattern regex against value.

        Parameters
        ----------
        value : str
            Value to match

        Returns
        -------
        re.Match
            re.Match object if the value matches the pattern. None otherwise.

        Example
        -------
        >>> p = Pattern("t_{my_date:date(%Y-%m-%d)}.grib")
        >>> p.match("t_2000-01-01.grib")
        <re.Match object; span=(0, 17), match='t_2000-01-01.grib'>

        >>> p = Pattern("t_{my_date:date(%Y-%m-%d)}.grib")
        >>> p.match("2000-01-01.grib")
        None

        >>> p = Pattern("{shortName}_{my_date:date(%Y-%m-%d)}.grib")
        >>> p.match("t_2000-01-01.grib")
        <re.Match object; span=(0, 17), match='t_2000-01-01.grib'>

        >>> p = Pattern("data/t/level")
        >>> p.match("data/t/level")
        <re.Match object; span=(0, 12), match='data/t/level'>
        >>> p.match("data/t/level/500")
        None
        """
        rx = self.regex
        return rx.match(value)

    def __repr__(self) -> str:
        t = "pattern:"
        for p in self.pattern:
            t += f"\n {p}"
        return t

    @cached_property
    def regex(self) -> re.Pattern:
        t = ""
        for p in self.pattern:
            if isinstance(p, Constant):
                t += p.value
            else:
                t += f"(?P<{p.name}>\S+)"

        t = rf"^{t}$"
        return re.compile(t)


class HivePattern:
    """Hive pattern.

    Parameters
    ----------
    pattern : str
        The hive pattern string.
    values : dict, optional
        Dictionary of values for substitution, by default None.

    Attributes
    ----------
    pattern : str
        The original pattern string.
    root : str
        The root directory of the pattern. This is the beginning of the path not containing
        any pattern parameters.
    rest : str
        The remaining part of the pattern after the root.
    params : list
        List of parameters in the pattern.
    dynamic_params : list
        List of parameters without user specified values in the pattern.
    fixed_single_params : dict
        Dictionary of user specified single value parameters.
    fixed_multi_keys : dict
        Dictionary of user specified multi value parameters.
    parts : list
        List of pattern parts. Each part is a Pattern object representing a part of the path.
    """

    def __init__(self, pattern: str, values: Optional[Dict[str, TypingAny]] = None) -> None:
        self.pattern = pattern
        values = values or {}
        values = dict(values)

        # substitute single values into the pattern
        pattern = Pattern(pattern)
        self.fixed_single_params = {}
        for k in list(values.keys()):
            v = values[k]
            LOG.debug(f" {k=} {v=}")
            if isinstance(v, (list, tuple)):
                if len(v) == 1:
                    self.fixed_single_params[k] = values.pop(k)[0]
            elif v:
                self.fixed_single_params[k] = values.pop(k)

        pattern = pattern._subpattern(self.fixed_single_params)

        # analyze path structure and turn each file path part into a
        # pattern
        path = Path(pattern)
        self.root = ""
        self.rest = ""
        path_parts = path.parts
        LOG.debug(f"{pattern=} {path_parts=}")

        parts = [Pattern(x) for x in path_parts]
        self.parts = []
        for i, part in enumerate(parts):
            if part.is_constant():
                self.root = os.path.join(self.root, part.pattern[0].value)
            else:
                self.rest = os.path.join(*path_parts[i:])
                self.parts = parts[i:]
                break

        self.params = list(self.fixed_single_params.keys())
        self.dynamic_params = []
        self.fixed_multi_params = {}
        for p in self.parts:
            for v in p.variables:
                if v.name is not self.params:
                    try:
                        s = v.substitute_many(values)
                        self.fixed_multi_params[v.name] = s
                    except ValueError:
                        self.dynamic_params.append(v.name)
                    self.params.append(v.name)

        assert len(self.fixed_multi_params) == len(values), f"{len(self.fixed_multi_params)} != {len(values)}"

        LOG.debug(f"root={self.root}")
        LOG.debug(f"rest={self.rest}")
        LOG.debug(f"params={self.params}")
        LOG.debug(f"dynamic_params={self.dynamic_params}")
        LOG.debug(f"fixed_single_params={self.fixed_single_params}")
        LOG.debug(f"fixed_multi_params={self.fixed_multi_params}")
        for p in self.parts:
            LOG.debug(f" {p=}")
            LOG.debug(f"   re={p.regex}")

    def scan(self, *args: Dict[str, TypingAny], **kwargs: TypingAny) -> List[str]:
        """Scan the file system for files matching the pattern.

        Parameters
        ----------
        args : tuple of dicts
            Positional dictionaries of parameters for scanning.
        kwargs : dict
            Additional keyword arguments for scanning.

        Returns
        -------
        list
            List of file paths matching the pattern.

        Raises
        ------
        ValueError
            If a parameter is not valid for the pattern.
        """
        params_in = {}
        for a in args:
            params_in.update(a)
        params_in.update(kwargs)

        for k in list(params_in.keys()):
            if isinstance(params_in[k], tuple):
                params_in[k] = list(params_in[k])
            elif not isinstance(params_in[k], list):
                params_in[k] = [params_in[k]]

        # determine param values to use
        params = {}
        for k, v in params_in.items():
            if k in self.fixed_single_params:
                if self.fixed_single_params[k] not in v:
                    return []

            elif k in self.fixed_multi_params:
                v1 = [v1 for v1 in v if v1 in self.fixed_multi_params[k]]
                if v1:
                    params[k] = v1
                else:
                    return []
            elif k in self.dynamic_params:
                params[k] = v
            else:
                raise ValueError(f"Invalid key '{k}' not in pattern")

        for k in params:
            params[k] = set([str(x) for x in params[k]])

        root_num = len(Path(self.root).parts)
        last = len(self.parts) - 1
        res = []

        # walk the file system
        for root, dirs, files in os.walk(self.root):
            # LOG.debug(f"walk: {root=}")
            index = len(Path(root).parts) - root_num
            # LOG.debug(f"{index=} {last=}")
            part = self.parts[index]

            # intermediate level
            if index != last:
                exclude = []
                for d in dirs:
                    g = self.collect(d, part, params)
                    if g is None:
                        exclude.append(d)
                # LOG.debug(f"   {exclude=}")
                if exclude:
                    dirs[:] = [d for d in dirs if d not in exclude]
                    continue

            # last level (collection)
            else:
                for file in files:
                    # LOG.debug(f"  {file=}")
                    d = self.collect(file, part, params)
                    if d:
                        res.append(os.path.join(root, file))
                        # LOG.debug("   match")

        return res

    def collect(self, file: str, part: Pattern, params: Dict[str, set[str]]) -> Optional[Dict[str, str]]:
        # LOG.debug(f"  match={file}")
        m = part.regex.match(file)
        if m:
            if part.is_constant():
                return {}

            group = m.groupdict()
            if len(group) == len(part.variables):
                for k, v in group.items():
                    if k in params:
                        # LOG.debug(f"  {k=} {v=} {params[k]=}")
                        if v not in params[k]:
                            return None
                return group
        return None
